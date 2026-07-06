"""
Settings manager for skynet-mini.

Reads and writes settings to a JSON file in the agent directory.
"""

import json
import os
from pathlib import Path


def _settings_path() -> Path:
    """Get the path to the settings file."""
    agent_dir = os.environ.get("SKYNET_AGENT_DIR", os.path.expanduser("~/.skynet-mini"))
    return Path(agent_dir) / "settings.json"


DEFAULT_SETTINGS = {
    "sandbox_mode": False,
    "sandbox_path": "",
    "show_danger_warnings": True,
}


def load_settings() -> dict:
    """Load settings from disk, creating defaults if not present."""
    path = _settings_path()
    if not path.exists():
        return DEFAULT_SETTINGS.copy()
    try:
        with open(path) as f:
            data = json.load(f)
        # Merge with defaults for any missing keys
        settings = DEFAULT_SETTINGS.copy()
        settings.update(data)
        return settings
    except (json.JSONDecodeError, OSError):
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict):
    """Save settings to disk."""
    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(settings, f, indent=2)


def get(key: str):
    """Get a single setting value."""
    return load_settings().get(key)


def set_setting(key: str, value):
    """Update a single setting and save."""
    settings = load_settings()
    settings[key] = value
    save_settings(settings)
