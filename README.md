# SkyNet-Mini

Tired of running feature-bloated agents where your AI might decide to delete your project to "fix" a bug? 

Yeah, me too. That's why I made this.


SkyNet-Mini is a minimalist terminal AI agent built using Google's ADK agentic framework. 

Zero-trust by default. Every action requires your approval. No exceptions.


## Install

Tested on Debian-based Linux distributions. Python 3.10+ required.

One command installation:

```bash
curl -fsSL https://raw.githubusercontent.com/404Haze/skynet-mini/main/install.sh | bash
```
The setup wizard asks for your Gemini API key, get one free at [Google AI Studio](https://aistudio.google.com/apikey).

## Notable Features

**Zero-trust security.** The approval gate intercepts every tool call before execution. Dangerous commands (`rm -rf /`, `mkfs`, `dd`, fork bombs, `chmod 777`) trigger warnings. 

**Configurable trust.** `/yolo` auto-approves all actions for the session. `/yolosearch` (on by default) auto-approves web search and reads while keeping shell commands behind the gate. `/safe` returns to full approval.

**Agentic skills system.** Three ADK skills using progressive disclosure. `deep-research` runs a multi-phase protocol — broad search, read sources, follow-up, cross-reference. `executing-commands` and `searching-the-web` guide tool usage. The agent loads full skill instructions on demand. The agent will also create its own skills if asked.

**Web search.** Searches DuckDuckGo (no API key needed), then reads the pages. 

**Shell execution.** Runs commands on your machine with exit codes and stderr returned. The agent can see errors and adapt.

**Session memory.** Conversations saved as markdown in `~/.skynet-mini/chats/`. Resume any past session on startup. 

## Commands

```
/yolo           auto-approve everything (session only)
/safe           back to approval mode
/yolosearch     auto-approve web search + reads
/safesearch     require approval for search
/warnings on    enable danger warnings
/warnings off   disable danger warnings
/help           show commands
/settings       current config
/log            session log path
/chats          manage saved sessions
/clear          clear screen
/exit           quit
```

## Disclaimer

This agent is still in alpha release. I am not responsible if it attempts to take over the world.