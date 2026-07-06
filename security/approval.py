"""Approval gate — intercepts every tool call for y/n approval."""

from security.dangerous import is_dangerous

_log_fn = None


def set_logger(fn):
    global _log_fn
    _log_fn = fn


def _shorten_cmd(cmd: str, max_len: int = 60) -> str:
    """Shorten a shell command for display, stripping newlines."""
    # Replace newlines with spaces so display stays clean
    cmd = cmd.replace("\\n", " ").replace("\n", " ")
    # Collapse multiple spaces
    while "  " in cmd:
        cmd = cmd.replace("  ", " ")
    cmd = cmd.strip()
    if len(cmd) <= max_len:
        return cmd
    if "&&" in cmd or ";" in cmd:
        names = []
        for part in cmd.replace(";", "&&").split("&&"):
            name = part.strip().split()[0] if part.strip().split() else ""
            if name:
                names.append(name)
        result = " && ".join(names)
        if len(result) > max_len:
            result = result[:max_len - 3] + "..."
        return result
    # Truncate at word boundary
    truncated = cmd[:max_len - 3]
    last_space = truncated.rfind(" ")
    if last_space > max_len // 2:
        truncated = truncated[:last_space]
    return truncated + "..."


def _format_tool(tool_name: str, args: dict) -> str:
    """Format a tool call for display, matching the SkyNet-Mini style."""
    if tool_name == "run_shell" and "command" in args:
        cmd = _shorten_cmd(args["command"])
        return f"[Running: {cmd}]"
    elif tool_name == "web_search":
        q = args.get("query", "")
        return f'[Searched the web for "{q}"]'
    elif tool_name == "web_read":
        u = args.get("url", "")
        return f"[Read link: {u}]"
    elif tool_name == "load_skill":
        name = args.get("name", args.get("skill_name", ""))
        return f"[Loaded skill: {name}]" if name else "[Loaded skill]"
    elif tool_name == "list_skills":
        return "[Reading available skills]"
    elif tool_name in ("load_skill_resource", "run_skill_script"):
        detail = args.get("name", args.get("skill_name", ""))
        return f"[Using: {tool_name} {detail}]" if detail else f"[Using: {tool_name}]"
    else:
        return f"[{tool_name}]"


class ApprovalGate:
    def __init__(self, show_warnings: bool = True):
        self.yolo = False
        self.trust_search = False
        self.show_warnings = show_warnings

    def enable_yolo(self) -> str:
        return (
            "Warning: Agent will run commands without asking. Only use in VM.\n"
            "Type YES to confirm.\n"
            "><> "
        )

    def activate_yolo(self): self.yolo = True
    def deactivate_yolo(self): self.yolo = False
    def toggle_warnings(self, enabled: bool): self.show_warnings = enabled

    def request_approval(self, tool_name: str, args: dict) -> bool:
        line = _format_tool(tool_name, args)

        if self.yolo:
            if _log_fn: _log_fn(f"[yolo] {tool_name}")
            print(line)
            return True

        # Skill operations are always auto-approved — internal bookkeeping
        if tool_name in ("load_skill", "list_skills", "load_skill_resource", "run_skill_script"):
            if _log_fn: _log_fn(f"[skill] {tool_name}")
            print(line)
            return True

        if self.trust_search and tool_name in ("web_search", "web_read"):
            if _log_fn: _log_fn(f"[trust] {tool_name}")
            print(line)
            return True
        if _log_fn: _log_fn(f"--- {line}")

        print(line)

        if tool_name == "run_shell" and "command" in args and self.show_warnings:
            dangerous, matches = is_dangerous(args["command"])
            for _, warning in matches:
                print(f"WARNING: {warning}")

        print("Approve? [y/n]")
        while True:
            try:
                r = input("><> ").strip().lower()
                if r in ("y", "yes"):
                    if _log_fn: _log_fn("  approved")
                    return True
                if r in ("n", "no"):
                    if _log_fn: _log_fn("  denied")
                    return False
            except (EOFError, KeyboardInterrupt):
                if _log_fn: _log_fn("  cancelled")
                return False


approval_gate: ApprovalGate = None  # type: ignore


def get_approval_gate() -> ApprovalGate:
    global approval_gate
    if approval_gate is None:
        approval_gate = ApprovalGate()
    return approval_gate
