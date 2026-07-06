#!/usr/bin/env bash
# SkyNet-Mini installer — one-liner: curl -fsSL <url>/install.sh | bash
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'
BOLD='\033[1m'

info()  { echo -e "  ${CYAN}→${NC} $*"; }
ok()    { echo -e "  ${GREEN}✓${NC} $*"; }
err()   { echo -e "  ${RED}✗${NC} $*"; }
step()  { echo -e "\n${BOLD}${CYAN}${1}${NC}"; }

# ── Python check ──────────────────────────────────────────────
step "Checking Python..."
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        ver=$("$cmd" --version 2>&1 | grep -oP '\d+\.\d+')
        [ -n "$ver" ] && [ "${ver%%.*}" -ge 3 ] && PYTHON="$cmd" && break
    fi
done
[ -z "$PYTHON" ] && err "Python 3 not found. Install: apt install python3" && exit 1
ok "Found $PYTHON $ver"

# ── System deps ───────────────────────────────────────────────
step "System dependencies..."
MISSING=""
command -v pip3 &>/dev/null || MISSING=" python3-pip"
[ -n "$MISSING" ] && info "Installing:$MISSING ..." && sudo apt-get update -qq && sudo apt-get install -y -qq $MISSING 2>/dev/null
ok "System dependencies ready"

# ── Agent directory ───────────────────────────────────────────
AGENT_DIR="${SKYNET_AGENT_DIR:-$HOME/.skynet-mini}"
VENV_DIR="${AGENT_DIR}/.venv"
info "Using agent directory: $AGENT_DIR"
mkdir -p "$AGENT_DIR"

# ── Virtual environment ───────────────────────────────────────
step "Python virtual environment..."
[ ! -d "$VENV_DIR" ] && info "Creating venv..." && "$PYTHON" -m venv "$VENV_DIR" 2>&1 | sed 's/^/    /'
ok "Venv ready"

# ── Python dependencies ───────────────────────────────────────
step "Installing Python dependencies..."
PIP="$VENV_DIR/bin/pip"
"$PIP" install --quiet --upgrade pip 2>/dev/null
"$PIP" install --quiet google-adk ddgs python-dotenv rich 2>&1 | grep -v "^Requirement already" | sed 's/^/    /' || true
ok "google-adk, ddgs, python-dotenv, rich"

# ── Install agent files ───────────────────────────────────────
step "Installing agent files..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || echo "")"
if [ -z "$SCRIPT_DIR" ] || [ ! -f "$SCRIPT_DIR/main.py" ]; then
    for d in "$HOME/Downloads/skynet-mini" "$(pwd)"; do
        [ -f "$d/main.py" ] && SCRIPT_DIR="$d" && break
    done
fi
[ -z "$SCRIPT_DIR" ] || [ ! -f "$SCRIPT_DIR/main.py" ] && err "Cannot find source files." && exit 1

if [ "$SCRIPT_DIR" != "$AGENT_DIR" ]; then
    info "Copying from $SCRIPT_DIR → $AGENT_DIR"
    cp "$SCRIPT_DIR"/*.py "$AGENT_DIR"/ 2>/dev/null || true
    cp "$SCRIPT_DIR"/SOUL.md "$AGENT_DIR"/ 2>/dev/null || true
    cp -r "$SCRIPT_DIR"/tools "$AGENT_DIR"/ 2>/dev/null || true
    cp -r "$SCRIPT_DIR"/security "$AGENT_DIR"/ 2>/dev/null || true
    cp -r "$SCRIPT_DIR"/skills "$AGENT_DIR"/ 2>/dev/null || true
    cp "$SCRIPT_DIR"/skynet.sh "$AGENT_DIR"/ 2>/dev/null || true
fi
ok "Agent files in place"

# ── Global shortcut ───────────────────────────────────────────
step "Global shortcut..."
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"
SHORTCUT="$BIN_DIR/skynet"
cat > "$SHORTCUT" << 'SKYNETEOF'
#!/usr/bin/env bash
AGENT_DIR="${SKYNET_AGENT_DIR:-$HOME/.skynet-mini}"
# Check for sandbox mode
SANDBOX_USER=""
[ -f "$AGENT_DIR/settings.json" ] && SANDBOX_USER=$(python3 -c "import json;d=json.load(open('$AGENT_DIR/settings.json'));print(d.get('sandbox_user',''))" 2>/dev/null || echo "")
if [ -n "$SANDBOX_USER" ]; then
    exec sudo -u "$SANDBOX_USER" "$AGENT_DIR/.venv/bin/python3" "$AGENT_DIR/main.py" "$@"
else
    VENV_PYTHON="$AGENT_DIR/.venv/bin/python3"
    [ -f "$VENV_PYTHON" ] || VENV_PYTHON="$HOME/Downloads/skynet-mini/.venv/bin/python3"
    [ -f "$VENV_PYTHON" ] || VENV_PYTHON="python3"
    cd "$AGENT_DIR" && exec "$VENV_PYTHON" main.py "$@"
fi
SKYNETEOF
chmod +x "$SHORTCUT"
ok "Shortcut: $SHORTCUT"

# Check PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    SHELL_RC="$HOME/.bashrc"
    grep -q "$BIN_DIR" "$SHELL_RC" 2>/dev/null || echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$SHELL_RC"
    info "Added $BIN_DIR to PATH in ~/.bashrc"
    echo -e "\n  ${BOLD}Run this to use 'skynet' now:${NC}  export PATH=\"$BIN_DIR:\$PATH\""
fi

# ── Done ──────────────────────────────────────────────────────
echo -e "\n${BOLD}${GREEN}Installation complete.${NC}"
