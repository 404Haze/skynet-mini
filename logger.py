"""Session logger — writes everything to a timestamped log file."""

import os
from datetime import datetime
from pathlib import Path


class Logger:
    def __init__(self, agent_dir: str):
        log_dir = Path(agent_dir) / "logs"
        log_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = log_dir / f"session_{ts}.log"
        self._file = open(self.path, "a")
        self._write(f"session started {datetime.now().isoformat()}")

    def _write(self, line: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self._file.write(f"[{ts}] {line}\n")
        self._file.flush()

    def user(self, text: str):
        self._write(f"><> {text}")

    def agent(self, text: str):
        for line in text.split("\n"):
            self._write(f"  {line}")

    def tool_approval(self, tool: str, args: dict):
        self._write(f"--- approval: {tool} ---")

    def tool_approved(self, tool: str):
        self._write(f"  approved: {tool}")

    def tool_denied(self, tool: str):
        self._write(f"  denied: {tool}")

    def yolo_auto(self, tool: str):
        self._write(f"  [yolo] {tool}")

    def error(self, msg: str):
        self._write(f"  error: {msg}")

    def command(self, cmd: str):
        self._write(f"><> /{cmd}")

    def close(self):
        self._write(f"session ended {datetime.now().isoformat()}")
        self._file.close()
