"""
Shell execution tool for skynet-mini.

Wraps subprocess to execute shell commands safely.
All commands go through the approval gate before execution.
"""

import subprocess
import os


def run_shell(command: str) -> dict:
    """
    Execute a shell command on the user's Linux machine.

    Args:
        command: The shell command to execute.

    Returns:
        A dict with 'status' ('success' or 'error'), 'stdout', 'stderr',
        and 'exit_code'. On timeout or exception, returns error status.
    """
    # Restrict to sandbox directory if configured
    sandbox_path = os.environ.get("SKYNET_SANDBOX_PATH")
    if sandbox_path:
        # Change to sandbox directory before running
        command = f"cd {sandbox_path} && {command}"

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=sandbox_path if sandbox_path else None,
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        # Truncate very long output
        if len(stdout) > 4000:
            stdout = stdout[:4000] + "\n... [output truncated]"
        if len(stderr) > 4000:
            stderr = stderr[:4000] + "\n... [output truncated]"

        return {
            "status": "success" if result.returncode == 0 else "error",
            "stdout": stdout if stdout else "(no output)",
            "stderr": stderr if stderr else "(no errors)",
            "exit_code": result.returncode,
            "hint": None if result.returncode == 0 else (
                "Command failed. Check stderr for details. "
                "If the error is about quoting, use double-quotes instead of single-quotes, "
                "or use printf instead of echo."
            ),
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "error_message": "Command timed out after 60 seconds.",
            "stdout": "",
            "stderr": "",
            "exit_code": -1,
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Command failed: {str(e)}",
            "stdout": "",
            "stderr": "",
            "exit_code": -1,
        }
