#!/usr/bin/env bash
# SkyNet-Mini launcher — symlink or copy to ~/.local/bin/skynet
set -e

AGENT_DIR="${SKYNET_AGENT_DIR:-$HOME/.skynet-mini}"
VENV_PYTHON="${SKYNET_VENV:-$HOME/Downloads/skynet-mini/.venv/bin/python3}"

if [ ! -f "$AGENT_DIR/main.py" ]; then
    echo "error: SkyNet-Mini not found at $AGENT_DIR"
    echo "run the setup wizard first: python3 -c 'from main import run_setup_wizard; run_setup_wizard()'"
    exit 1
fi

if [ ! -f "$VENV_PYTHON" ]; then
    VENV_PYTHON="python3"
fi

cd "$AGENT_DIR"
exec "$VENV_PYTHON" main.py "$@"
