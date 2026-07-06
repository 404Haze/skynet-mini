"""Chat manager — saves and resumes conversations as markdown files."""

import os
import re
from datetime import datetime
from pathlib import Path


class ChatManager:
    def __init__(self, agent_dir: str, resume_file: str = None):
        self.chats_dir = Path(agent_dir) / "chats"
        self.chats_dir.mkdir(exist_ok=True)
        if resume_file:
            self.current_file = self.chats_dir / resume_file
        else:
            self._start_new()

    def _start_new(self):
        """Create a new chat file."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_file = self.chats_dir / f"chat_{ts}.md"
        self._append(f"# SkyNet-Mini\n_started {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n")

    def _append(self, line: str):
        with open(self.current_file, "a") as f:
            f.write(line + "\n")

    def save_turn(self, user_msg: str, response: str, think_time: float):
        """Save a complete exchange."""
        if think_time >= 60:
            think = f"[Thought for {think_time/60:.2f} minutes]"
        else:
            think = f"[Thought for {think_time:.1f} seconds]"
        self._append(f"\n><> {user_msg}\n")
        self._append(f"\nSkyNet-Mini\n{think}\n")
        self._append(f"\n{response}\n")
        self._append("\n---\n")

    @property
    def path(self) -> str:
        return str(self.current_file)

    @classmethod
    def list_chats(cls, agent_dir: str) -> list[tuple[str, str, str]]:
        """Return list of (filename, title, date) for existing chats."""
        chats_dir = Path(agent_dir) / "chats"
        if not chats_dir.exists():
            return []
        results = []
        for f in sorted(chats_dir.glob("chat_*.md"), reverse=True):
            # Extract first user message as title
            try:
                content = f.read_text()
                first_msg = ""
                date_str = ""
                m = re.search(r'><> (.+)', content)
                if m:
                    first_msg = m.group(1)[:60]
                m = re.search(r'_started (.+)_', content)
                if m:
                    date_str = m.group(1)
                results.append((f.name, first_msg or "(empty)", date_str))
            except Exception:
                results.append((f.name, "(unreadable)", ""))
        return results

    @classmethod
    def load_history(cls, agent_dir: str, filename: str) -> list[tuple[str, str]]:
        """Load chat history as list of (role, message) tuples.
        Returns messages that can be replayed into a new session.
        """
        path = Path(agent_dir) / "chats" / filename
        if not path.exists():
            return []
        content = path.read_text()
        exchanges = []
        # Parse the markdown: extract user messages and agent responses
        parts = re.split(r'\n><> ', content)
        for part in parts[1:]:  # Skip header
            lines = part.strip().split('\n')
            if not lines:
                continue
            user_msg = lines[0].strip()
            # Find agent response after SkyNet-Mini header
            response_parts = []
            in_response = False
            for line in lines[1:]:
                if line.startswith('SkyNet-Mini'):
                    in_response = True
                    continue
                if line.startswith('[Thought for'):
                    continue
                if line.startswith('---'):
                    break
                if in_response and line.strip():
                    response_parts.append(line)
            response = '\n'.join(response_parts).strip()
            if user_msg:
                exchanges.append(("user", user_msg))
            if response:
                exchanges.append(("assistant", response))
        return exchanges
