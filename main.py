#!/usr/bin/env python3
"""SkyNet-Mini — terminal AI agent with human-in-the-loop safety."""

import asyncio
import io
import logging
import os
import re
import sys
import time
import uuid
import warnings
from contextlib import aclosing
from pathlib import Path

warnings.filterwarnings("ignore", category=UserWarning, module="google.adk")
warnings.filterwarnings("ignore", category=RuntimeWarning)
logging.getLogger("google_adk").setLevel(logging.ERROR)
logging.getLogger("google.adk").setLevel(logging.ERROR)

from dotenv import load_dotenv
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agent import create_agent
from security.approval import ApprovalGate
from settings import load_settings, set_setting
from logger import Logger
from chat_manager import ChatManager
from rich.console import Console
from rich.markdown import Markdown

console = Console()

BANNER = "[SkyNet-Mini Online]"

HELP_TEXT = """  session
    /yolo           auto-approve all actions (session only)
    /safe           return to approval mode
    /safesearch     auto-approve web search and read
    /yolosearch     require approval for search
    /warnings on    enable danger warnings
    /warnings off   disable danger warnings

  info
    /help           show this
    /settings       show current settings
    /log            show session log path
    /chats          manage saved chats

  control
    /clear          clear screen
    /exit, /quit    quit"""

log: Logger = None


def _fmt_date(date_str: str) -> str:
    """Convert '2026-07-06 12:49' to 'July 6th'."""
    try:
        from datetime import datetime
        dt = datetime.strptime(date_str.split(" ")[0], "%Y-%m-%d")
        day = dt.day
        suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        return dt.strftime(f"%B {day}{suffix}")
    except Exception:
        return date_str


# ─── setup ─────────────────────────────────────────────────────────

def setup_environment():
    agent_dir = os.environ.get("SKYNET_AGENT_DIR", os.path.expanduser("~/.skynet-mini"))
    env_path = Path(agent_dir) / ".env"
    load_dotenv(env_path) if env_path.exists() else load_dotenv()
    os.environ.setdefault("SKYNET_AGENT_DIR", agent_dir)


def check_api_key():
    key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        print("error: no Gemini API key found.")
        print("set GOOGLE_API_KEY in ~/.skynet-mini/.env")
        sys.exit(1)
    os.environ.setdefault("GOOGLE_API_KEY", key)


# ─── agent runner ──────────────────────────────────────────────────

async def run_agent_async(msg: str, runner: Runner, uid: str, sid: str):
    content = types.Content(role="user", parts=[types.Part(text=msg)])
    parts = []
    async with aclosing(runner.run_async(user_id=uid, session_id=sid, new_message=content)) as agen:
        async for event in agen:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        parts.append(part.text)
    return "\n".join(parts) if parts else ""


def run_agent_sync(msg: str, runner: Runner, uid: str, sid: str) -> tuple[str, float]:
    """Returns (response_text, elapsed_seconds)."""
    t0 = time.time()
    response = asyncio.run(run_agent_async(msg, runner, uid, sid))
    elapsed = time.time() - t0
    return response, elapsed


# ─── commands ──────────────────────────────────────────────────────

def handle_command(cmd: str, gate: ApprovalGate, settings: dict) -> bool:
    cmd = cmd.strip()

    if cmd in ("/exit", "/quit"):
        print("[SkyNet offline]")
        sys.exit(0)

    elif cmd == "/help":
        print(HELP_TEXT)
        return True

    elif cmd == "/log":
        if log:
            # Count entries in log
            try:
                with open(log.path) as f:
                    entries = sum(1 for _ in f)
            except Exception:
                entries = "?"
            print(f"[Session log: {log.path}]")
            print(f"{entries} entries since session start.")
        else:
            print("no log active")
        return True

    elif cmd == "/chats":
        adir = os.environ.get("SKYNET_AGENT_DIR", os.path.expanduser("~/.skynet-mini"))
        chats = ChatManager.list_chats(adir)
        if not chats:
            print("no saved chats")
        else:
            print(f"\nYou have {len(chats)} saved chat(s):")
            for i, (fname, title, date) in enumerate(chats):
                print(f"  [{i+1}] {title} ({date})")
            print("Type a number to delete, or anything else to cancel.")
            try:
                choice = input("><> ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(chats):
                    fname = chats[idx][0]
                    (Path(adir) / "chats" / fname).unlink()
                    print(f"Deleted: {fname}")
            except (ValueError, IndexError):
                pass
        return True

    elif cmd == "/yolo":
        warning = gate.enable_yolo()
        response = input(warning).strip()
        if response == "YES":
            gate.activate_yolo()
            if log: log.command("YOLO activated")
            print("[YOLO mode activated]")
        else:
            print("\nYOLO not activated.\n")
        return True

    elif cmd == "/safe":
        gate.deactivate_yolo()
        if log: log.command("safe")
        print("[Safe mode activated]")
        return True

    elif cmd == "/warnings on":
        gate.toggle_warnings(True)
        set_setting("show_danger_warnings", True)
        print("danger warnings: on")
        return True

    elif cmd == "/warnings off":
        gate.toggle_warnings(False)
        set_setting("show_danger_warnings", False)
        print("danger warnings: off")
        return True

    elif cmd == "/safesearch":
        gate.trust_search = True
        set_setting("trust_search", True)
        print("[Safesearch: on] web_search and web_read auto-approved")
        return True

    elif cmd == "/yolosearch":
        gate.trust_search = False
        set_setting("trust_search", False)
        print("[Safesearch: off]")
        return True

    elif cmd == "/settings":
        print()
        print(f"safety: {'YOLO' if gate.yolo else 'default'}")
        print(f"warnings: {'on' if gate.show_warnings else 'off'}")
        print(f"safesearch: {'on' if gate.trust_search else 'off'}")
        if settings.get("sandbox_mode"):
            print(f"sandbox: {settings.get('sandbox_path', '?')}")
        if log: print(f"log: {log.path}")
        return True

    elif cmd == "/clear":
        os.system("clear" if os.name != "nt" else "cls")
        print(BANNER)
        return True

    return False


# ─── wizard ────────────────────────────────────────────────────────

def run_setup_wizard():
    print("SkyNet-Mini setup\n")
    sandbox_mode = False
    sandbox_path = ""

    print("[1] sandboxed — restricted to one folder")
    print("[2] unsandboxed — full system access\n")
    while True:
        c = input("choice (1/2): ").strip()
        if c == "1": sandbox_mode = True; break
        if c == "2": sandbox_mode = False; break

    if sandbox_mode:
        sandbox_path = input("\nfolder path: ").strip()
        sandbox_path = os.path.expanduser(sandbox_path)
        if not sandbox_path:
            print("no path — defaulting to unsandboxed.")
            sandbox_mode = False
        else:
            os.makedirs(sandbox_path, exist_ok=True)
            agent_dir = os.path.join(sandbox_path, ".skynet-mini")
    else:
        agent_dir = os.path.expanduser("~/.skynet-mini")

    os.environ["SKYNET_AGENT_DIR"] = agent_dir
    os.makedirs(agent_dir, exist_ok=True)

    api_key = input("gemini api key: ").strip()
    if api_key:
        with open(os.path.join(agent_dir, ".env"), "w") as f:
            f.write(f'GOOGLE_API_KEY="{api_key}"\n')
        print("key saved.")

    _copy_project_files(agent_dir)

    from settings import save_settings as save_s
    save_s({"sandbox_mode": sandbox_mode, "sandbox_path": sandbox_path if sandbox_mode else "", "show_danger_warnings": True})

    print(f"\ndone. run with: cd {agent_dir} && python3 main.py\n")


def _copy_project_files(agent_dir: str):
    src, dst = Path(__file__).parent, Path(agent_dir)
    import shutil
    for f in ["main.py", "agent.py", "settings.py", "SOUL.md", "logger.py"]:
        if (src / f).exists() and not (dst / f).exists():
            shutil.copy2(src / f, dst / f)
    for d in ["tools", "security", "skills"]:
        if (src / d).exists() and not (dst / d).exists():
            shutil.copytree(src / d, dst / d)


# ─── main ──────────────────────────────────────────────────────────

def main():
    global log

    if "--wizard" in sys.argv:
        run_setup_wizard()
        return

    if "--sandbox" in sys.argv:
        idx = sys.argv.index("--sandbox")
        if idx + 1 < len(sys.argv):
            os.environ["SKYNET_SANDBOX_PATH"] = sys.argv[idx + 1]
        else:
            print("error: --sandbox needs a path")
            sys.exit(1)

    setup_environment()
    check_api_key()

    settings = load_settings()
    agent_dir = os.environ["SKYNET_AGENT_DIR"]
    os.chdir(agent_dir)

    log = Logger(agent_dir)
    from security.approval import set_logger
    set_logger(lambda msg: log._write(msg))

    gate = ApprovalGate(show_warnings=settings.get("show_danger_warnings", True))
    import security.approval as app_mod
    app_mod.approval_gate = gate

    agent = create_agent()
    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name="skynet_mini", session_service=session_service)

    user_id = os.environ.get("USER", "user")
    session_id = str(uuid.uuid4())
    asyncio.run(session_service.create_session(
        app_name="skynet_mini", user_id=user_id, session_id=session_id))

    print(BANNER)
    print(f"log: {log.path}")

    # Show loaded skills
    skills_dir = Path(agent_dir) / "skills"
    if skills_dir.exists():
        names = sorted([d.name for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()])
        if names:
            print(f"skills: {', '.join(names)}")

    # Chat manager — check for existing chats
    chat = None
    resume_context = ""
    existing = ChatManager.list_chats(agent_dir)
    if existing:
        print(f"\nAvailable sessions:")
        print("  [n] New session")
        for i, (fname, title, date) in enumerate(existing[:5]):
            print(f"  [{i+1}] {title} ({_fmt_date(date)})")
        print()
        choice = input("Which session shall we start?\n><> ").strip().lower()
        if choice and choice != "n":
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(existing):
                    fname = existing[idx][0]
                    chat_path = Path(agent_dir) / "chats" / fname
                    resume_context = chat_path.read_text()
                    # Strip header lines
                    resume_context = re.sub(r'^# SkyNet-Mini\n_started.*_\n', '', resume_context)
                    resume_context = resume_context.strip()
                    print(f"\nResumed: {fname}")
                    if resume_context:
                        print(f"  ({len(resume_context)} chars of context loaded)\n")
            except (ValueError, IndexError):
                pass
    if chat is None:
        chat = ChatManager(agent_dir)
    else:
        chat = ChatManager(agent_dir, resume_file=fname)

    while True:
        try:
            user_input = input("\n><> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[SkyNet offline]\n")
            log.close()
            break

        if not user_input:
            continue

        log.user(user_input)

        if user_input.startswith("/"):
            if handle_command(user_input, gate, settings):
                continue

        # Prepend resume context on first message
        if resume_context:
            user_input = f"[Previous conversation]\n{resume_context}\n\n[Continue from above]\n{user_input}"
            resume_context = ""  # Only once

        try:
            old_stderr = sys.stderr
            captured_stderr = io.StringIO()
            sys.stderr = captured_stderr
            try:
                response, elapsed = run_agent_sync(user_input, runner, user_id, session_id)
            finally:
                sys.stderr = old_stderr
            if response:
                log.agent(response)
                # SkyNet-Mini header + think time
                if elapsed >= 60:
                    think = f"[Thought for {elapsed/60:.2f} minutes]"
                else:
                    think = f"[Thought for {elapsed:.1f} seconds]"
                print(f"\nSkyNet-Mini\n{think}\n")
                console.print(Markdown(response))
                chat.save_turn(user_input, response, elapsed)
        except Exception as e:
            err_msg = str(e).strip()
            if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
                err_msg = "api rate limited, try again soon"
            elif "UNAVAILABLE" in err_msg or "503" in err_msg:
                err_msg = "api overloaded, try again soon"
            elif "api key" in err_msg.lower():
                err_msg = "invalid api key"
            elif not err_msg:
                stderr_text = captured_stderr.getvalue().strip()
                if "RESOURCE_EXHAUSTED" in stderr_text or "429" in stderr_text:
                    err_msg = "api rate limited, try again soon"
                elif "UNAVAILABLE" in stderr_text or "503" in stderr_text:
                    err_msg = "api overloaded, try again soon"
                else:
                    err_msg = "api error, try again"
            log.error(err_msg)
            print(f"\n{err_msg}")


if __name__ == "__main__":
    main()
