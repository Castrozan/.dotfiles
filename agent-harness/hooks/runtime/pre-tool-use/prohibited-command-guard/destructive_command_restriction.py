import json
import os
from pathlib import Path

from destructive_command_patterns import DESTRUCTIVE_PATTERNS_BY_TOOL
from interactive_session_detection import CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER

AGENTS_DENIED_DESTRUCTIVE_COMMANDS_FILE = (
    Path.home() / "clawde" / "agents-denied-destructive-commands.json"
)


def agents_denied_destructive_commands() -> frozenset:
    try:
        declared_agents = json.loads(
            AGENTS_DENIED_DESTRUCTIVE_COMMANDS_FILE.read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        return frozenset()
    if not isinstance(declared_agents, list):
        return frozenset()
    return frozenset(
        agent_name for agent_name in declared_agents if isinstance(agent_name, str)
    )


def destructive_patterns_for_this_session(tool_name: str) -> list:
    running_agent_name = os.environ.get(CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER, "")
    if not running_agent_name:
        return []
    if running_agent_name not in agents_denied_destructive_commands():
        return []
    return DESTRUCTIVE_PATTERNS_BY_TOOL.get(tool_name, [])
