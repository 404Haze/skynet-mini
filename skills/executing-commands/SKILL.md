---
name: executing-commands
description: >
  Use when the user asks you to run commands, install software,
  manage files, or perform any system operation on their Linux
  machine. Triggers on requests like "install", "run", "create",
  "delete", "check", "show me", "list", "find".
---

# Executing Shell Commands

Use the `run_shell` tool to execute commands on the user's Linux machine.

## When to use this skill

- User asks to install, update, or remove software
- User asks to create, edit, delete, or move files
- User asks to check system status (disk space, processes, etc.)
- User asks to run a script or program
- User asks to list directory contents or find files

## How to execute commands safely

1. EXPLAIN what the command will do BEFORE calling it
2. Call `run_shell(command="the exact command")`
3. Report the result clearly — show relevant output, hide noise
4. If the command fails, explain the error and suggest a fix

## Safety rules

- Prefer non-destructive alternatives (e.g., ls before rm)
- Never combine multiple risky operations in one command
- Don't run background processes or daemons
- Commands have a 60-second timeout — keep them focused
- For long output, summarize the key parts
