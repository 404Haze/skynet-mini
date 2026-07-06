"""
Dangerous shell command detection for skynet-mini.

Uses regex patterns to identify potentially harmful shell commands
and returns warnings when matches are found.
"""

import re
from typing import List, Tuple

# (pattern_name, regex_pattern, warning_message)
DANGEROUS_PATTERNS: List[Tuple[str, str, str]] = [
    (
        "recursive_force_remove",
        r"rm\s+.*(-rf|-fr|--recursive\s+--force|--force\s+--recursive)",
        "Recursive force remove — deletes files/directories permanently without confirmation",
    ),
    (
        "make_filesystem",
        r"\bmkfs(\.\w+)?\s+",
        "Creates a filesystem — will destroy existing data on the target device",
    ),
    (
        "disk_write_dd",
        r"\bdd\s+.*of=/dev/",
        "Direct disk write — can overwrite partitions or entire drives",
    ),
    (
        "fork_bomb",
        r":\(\)\s*\{\s*:\|:&\s*\};\s*:",
        "Fork bomb — will crash the system by exhausting processes",
    ),
    (
        "overwrite_block_device",
        r".*\s*>\s*/dev/sd[a-z]+\d*",
        "Redirecting output to a block device — can corrupt the filesystem",
    ),
    (
        "chmod_recursive_777",
        r"\bchmod\s+.*(-R|--recursive).*777|chmod\s+.*777.*(-R|--recursive)",
        "Recursive chmod 777 — gives everyone full permissions, major security risk",
    ),
    (
        "fdisk_partition",
        r"\bfdisk\s+",
        "Disk partitioning tool — can destroy partition tables and data",
    ),
    (
        "pipe_to_shell",
        r"\b(wget|curl)\s+.+\s*\|\s*(sh|bash)\b",
        "Downloading and piping directly to shell — could execute malicious code",
    ),
    (
        "shutdown_reboot",
        r"\b(shutdown|reboot|halt|poweroff|init\s+[06])(\s|$)",
        "System shutdown or reboot command",
    ),
    (
        "crontab_clear",
        r"\bcrontab\s+-r\b",
        "Removes all cron jobs — no undo, no confirmation",
    ),
    (
        "move_root_to_devnull",
        r"\bmv\s+.*/\s+/dev/null",
        "Moving root to /dev/null — will destroy the filesystem",
    ),
    (
        "sudo_dangerous",
        r"\bsudo\s+.*\brm\s+-rf\s+/",
        "Sudo combined with rm -rf / — can wipe the entire system",
    ),
    (
        "chown_root_recursive",
        r"\bchown\s+.*(-R|--recursive).*root:root\s+/",
        "Recursively changing ownership to root — can break the system",
    ),
    (
        "format_mkfs_ext",
        r"\bmkfs\.(ext|fat|ntfs|xfs|btrfs)\s+/dev/",
        "Formatting a block device — all data on that device will be lost",
    ),
]


def is_dangerous(command: str) -> Tuple[bool, List[Tuple[str, str]]]:
    """
    Check if a shell command matches any dangerous patterns.

    Args:
        command: The shell command string to check.

    Returns:
        A tuple of (is_dangerous, matches) where matches is a list of
        (pattern_name, warning_message) for each matched pattern.
    """
    matches = []
    for name, pattern, warning in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            matches.append((name, warning))
    return bool(matches), matches
