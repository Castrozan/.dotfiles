import json
import os

from interactive_session_detection import CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER
from shell_command_invocation_position import (
    COMMAND_ARGUMENT_TERMINATOR_LOOKAHEAD,
    COMMAND_INVOCATION_POSITION_PREFIX,
)

AGENTS_DENIED_DESTRUCTIVE_COMMANDS_FILE = os.path.join(
    os.path.expanduser("~"), "clawde", "agents-denied-destructive-commands.json"
)

DESTRUCTIVE_COMMAND_DENIAL_REASON = (
    "This agent may not run destructive system commands. Ask the human to run it."
)

DESTRUCTIVE_COMMAND_PATTERN = (
    rf"{COMMAND_INVOCATION_POSITION_PREFIX}"
    rf"(?P<destructive_command>"
    rf"sudo|rm|rmdir|dd|mkfs(?:\.[^\s;&|]+)?|fdisk|shutdown|reboot|halt|poweroff"
    rf"){COMMAND_ARGUMENT_TERMINATOR_LOOKAHEAD}"
)

DESTRUCTIVE_BASH_COMMAND_PATTERNS = [
    (
        DESTRUCTIVE_COMMAND_PATTERN,
        DESTRUCTIVE_COMMAND_DENIAL_REASON,
        None,
        "destructive_command",
    ),
]

DESTRUCTIVE_PATTERNS_BY_TOOL = {
    "Bash": DESTRUCTIVE_BASH_COMMAND_PATTERNS,
}


def agents_denied_destructive_commands() -> frozenset:
    try:
        with open(
            AGENTS_DENIED_DESTRUCTIVE_COMMANDS_FILE, encoding="utf-8"
        ) as declaration_file:
            declared_agents = json.load(declaration_file)
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
