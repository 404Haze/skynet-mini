#!/usr/bin/env bash
# SkyNet-Mini installer — one-liner: curl -fsSL <url>/install.sh | bash
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'
BOLD='\033[1m'; DIM='\033[2m'

info()  { echo -e "  ${CYAN}→${NC} $*"; }
ok()    { echo -e "  ${GREEN}✓${NC} $*"; }
err()   { echo -e "  ${RED}✗${NC} $*"; }
step()  { echo -e "\n${BOLD}${CYAN}${1}${NC}"; }

echo -e "\n${BOLD}SkyNet-Mini Installer${NC}\n"

# ── Python check ──────────────────────────────────────────────
step "Checking Python..."
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        ver=$("$cmd" --version 2>&1 | grep -oP '\d+\.\d+')
        if [ -n "$ver" ]; then
            major=$(echo "$ver" | cut -d. -f1)
            if [ "$major" -ge 3 ]; then
                PYTHON="$cmd"; break
            fi
        fi
    fi
done
if [ -z "$PYTHON" ]; then
    err "Python 3 not found. Install it first: apt install python3"
    exit 1
fi
ok "Found $PYTHON $ver"

# ── System deps ───────────────────────────────────────────────
step "System dependencies..."
MISSING=""
command -v pip3 &>/dev/null || MISSING="$MISSING python3-pip"
if [ -n "$MISSING" ]; then
    info "Installing:$MISSING ..."
    sudo apt-get update -qq && sudo apt-get install -y -qq $MISSING 2>/dev/null || {
        err "Could not install$MISSING. Install manually: sudo apt install$MISSING"
        exit 1
    }
fi
ok "System dependencies ready"

# ── Agent directory ───────────────────────────────────────────
AGENT_DIR="${SKYNET_AGENT_DIR:-$HOME/.skynet-mini}"
VENV_DIR="${AGENT_DIR}/.venv"

info "Using agent directory: $AGENT_DIR"
mkdir -p "$AGENT_DIR"

# ── Virtual environment ───────────────────────────────────────
step "Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    info "Creating venv..."
    "$PYTHON" -m venv "$VENV_DIR" 2>&1 | sed 's/^/    /'
fi
ok "Venv ready: $VENV_DIR"

# ── Python dependencies ───────────────────────────────────────
step "Installing Python dependencies..."
PIP="$VENV_DIR/bin/pip"
info "Installing core packages..."
"$PIP" install --quiet --upgrade pip 2>/dev/null
"$PIP" install --quiet google-adk ddgs python-dotenv rich 2>&1 | grep -v "^Requirement already" | sed 's/^/    /' || true
ok "google-adk" && ok "ddgs (DuckDuckGo)" && ok "python-dotenv" && ok "rich (markdown)"

# ── Copy agent files ──────────────────────────────────────────
step "Installing agent files..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "$SCRIPT_DIR" != "$AGENT_DIR" ]; then
    info "Copying from $SCRIPT_DIR → $AGENT_DIR"
    cp -r "$SCRIPT_DIR"/*.py "$SCRIPT_DIR"/SOUL.md "$SCRIPT_DIR"/tools "$SCRIPT_DIR"/security "$SCRIPT_DIR"/skills "$SCRIPT_DIR"/skynet.sh "$AGENT_DIR"/ 2>/dev/null || true
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
VENV_PYTHON="$AGENT_DIR/.venv/bin/python3"
[ -f "$VENV_PYTHON" ] || VENV_PYTHON="$HOME/Downloads/skynet-mini/.venv/bin/python3"
[ -f "$VENV_PYTHON" ] || VENV_PYTHON="python3"
cd "$AGENT_DIR" && exec "$VENV_PYTHON" main.py "$@"
SKYNETEOF
chmod +x "$SHORTCUT"
ok "Shortcut: $SHORTCUT"

# Check PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    SHELL_RC="$HOME/.bashrc"
    if ! grep -q "$BIN_DIR" "$SHELL_RC" 2>/dev/null; then
        echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$SHELL_RC"
        info "Added $BIN_DIR to PATH in ~/.bashrc"
    fi
    echo -e "\n  ${BOLD}Run this to use 'skynet' now:${NC}"
    echo -e "  export PATH=\"$BIN_DIR:\$PATH\""
fi

# ── Wizard ────────────────────────────────────────────────────
step "Setup wizard..."
"$VENV_DIR/bin/python3" << 'WIZARD'
import sys, os, json
os.environ["SKYNET_AGENT_DIR"] = os.path.expanduser("~/.skynet-mini")
sys.path.insert(0, os.environ["SKYNET_AGENT_DIR"])
print()
skynet_key = input("  Gemini API key (leave blank to skip): ").strip()
if skynet_key:
    with open(os.path.join(os.environ["SKYNET_AGENT_DIR"], ".env"), "w") as f:
        f.write(f'GOOGLE_API_KEY="{skynet_key}"\n')
    print("  \033[0;32m✓\033[0m API key saved.")

settings_path = os.path.join(os.environ["SKYNET_AGENT_DIR"], "settings.json")
defaults = {"show_danger_warnings": True, "show_think_times": True, "markdown_render": True}
with open(settings_path, "w") as f:
    json.dump(defaults, f, indent=2)
print("  \033[0;32m✓\033[0m Settings initialized.")
WIZARD

# ── Done ──────────────────────────────────────────────────────
echo -e "\n${BOLD}${GREEN}SkyNet-Mini installed successfully.${NC}"
echo -e "\n  ${BOLD}Start with:${NC}"
echo -e "    ${CYAN}skynet${NC}"
echo -e "\n  Or directly:"
echo -e "    ${CYAN}cd ~/.skynet-mini && .venv/bin/python3 main.py${NC}"
echo
