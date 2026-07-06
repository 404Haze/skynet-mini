"""First-launch setup wizard for SkyNet-Mini."""

import os
import json
import subprocess
import sys
from pathlib import Path

GEMINI_URL = "https://aistudio.google.com/apikey"


def run_setup_wizard():
    """Full interactive setup wizard."""
    agent_dir = os.environ.get("SKYNET_AGENT_DIR", os.path.expanduser("~/.skynet-mini"))
    agent_dir = os.path.expanduser(agent_dir)
    os.makedirs(agent_dir, exist_ok=True)

    print("SkyNet-Mini Setup Wizard")

    # ── API Key ──────────────────────────────────────────────
    print(f"Get your free API key at: {GEMINI_URL}")
    api_key = input("Gemini API key: ").strip()

    env_path = Path(agent_dir) / ".env"
    if api_key:
        env_path.write_text(f'GOOGLE_API_KEY="{api_key}"\n')
    else:
        print("Skipped — add it later to .env")

    # ── Venv ─────────────────────────────────────────────────
    venv_dir = Path(agent_dir) / ".venv"
    if not venv_dir.exists():
        subprocess.run(["python3", "-m", "venv", str(venv_dir)], check=False)
        pip = str(venv_dir / "bin" / "pip")
        subprocess.run(
            [pip, "install", "--quiet",
             "google-adk", "ddgs", "python-dotenv", "rich"],
            check=False
        )

    # ── Save settings ────────────────────────────────────────
    settings = {
        "show_danger_warnings": True,
    }
    (Path(agent_dir) / "settings.json").write_text(json.dumps(settings, indent=2))

    # ── Install shortcut ─────────────────────────────────────
    bin_dir = os.path.expanduser("~/.local/bin")
    os.makedirs(bin_dir, exist_ok=True)
    shortcut = os.path.join(bin_dir, "skynet")
    Path(shortcut).write_text(f'''#!/usr/bin/env bash
AGENT_DIR="{agent_dir}"
cd "{agent_dir}" && exec ".venv/bin/python3" main.py "$@"
''')
    os.chmod(shortcut, 0o755)

    print(f"Setup complete! Run skynet to start.\n")
    sys.exit(0)
