"""
ADK agent definition for skynet-mini.

Defines the agent with tools, skills, and the human-in-the-loop
approval callback using ADK's before_tool_callback mechanism.
"""

import os
from pathlib import Path

from google.adk import Agent
from google.adk.skills import load_skill_from_dir
from google.adk.tools.skill_toolset import SkillToolset

from tools.web_search import web_search
from tools.web_read import web_read
from tools.shell import run_shell
from security.approval import get_approval_gate


def _get_agent_dir() -> Path:
    """Get the agent directory path."""
    return Path(os.environ.get("SKYNET_AGENT_DIR", os.path.expanduser("~/.skynet-mini")))


def _load_soul() -> str:
    """Load the SOUL.md system prompt."""
    soul_path = _get_agent_dir() / "SOUL.md"
    if soul_path.exists():
        return soul_path.read_text()
    # Fallback to project directory
    project_soul = Path(__file__).parent / "SOUL.md"
    if project_soul.exists():
        return project_soul.read_text()
    return "You are skynet-mini, a helpful terminal AI assistant."


def _load_skills():
    """Load skill directories as ADK SkillToolset."""
    agent_dir = _get_agent_dir()
    skills_dir = agent_dir / "skills"
    if not skills_dir.exists():
        skills_dir = Path(__file__).parent / "skills"

    loaded = []
    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                try:
                    skill = load_skill_from_dir(skill_dir)
                    loaded.append(skill)
                except Exception:
                    pass

    if loaded:
        return [SkillToolset(skills=loaded)]
    return []


def _approval_callback(tool, args: dict, tool_context) -> dict | None:
    """
    ADK before_tool_callback — intercepts every tool call.

    Returns None to let the tool execute, or a dict to skip
    execution and use the dict as the tool result.
    """
    gate = get_approval_gate()
    tool_name = getattr(tool, "name", tool.__class__.__name__)

    approved = gate.request_approval(tool_name, args)

    if approved:
        return None  # Let the tool execute normally

    return {
        "status": "denied",
        "message": "Tool call was denied by the user.",
    }


def create_agent() -> Agent:
    """Create and return the skynet-mini ADK agent."""
    soul = _load_soul()
    skill_toolsets = _load_skills()

    # Strengthen research instruction
    soul += (
        "\n\nRESEARCH RULE: When the user asks you to research, investigate, "
        "or find information about any topic, your FIRST action MUST be "
        "load_skill(\"deep-research\"). Always. Before anything else.\n"
    )

    tools = [web_search, web_read, run_shell]
    tools.extend(skill_toolsets)

    agent = Agent(
        name="skynet_mini",
        model=os.environ.get("SKYNET_MODEL", "gemini-flash-lite-latest"),
        description=(
            "A terminal AI assistant with mandatory human-in-the-loop "
            "safety approval. Can search the web and execute shell commands."
        ),
        instruction=soul,
        tools=tools,
        before_tool_callback=_approval_callback,
    )

    return agent
