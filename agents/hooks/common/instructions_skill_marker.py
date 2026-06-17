import os
import re
from pathlib import Path

STATE_DIRECTORY_OVERRIDE_ENVIRONMENT_VARIABLE = (
    "AGENT_INSTRUCTION_AUTHORING_ROUTER_STATE_DIRECTORY"
)


def resolve_state_directory():
    override = os.environ.get(STATE_DIRECTORY_OVERRIDE_ENVIRONMENT_VARIABLE)
    if override:
        return Path(override)
    return Path("/tmp")


def instructions_skill_loaded_marker_path(session_id):
    sanitized_session_id = re.sub(r"[^a-zA-Z0-9_-]+", "-", session_id or "unknown")
    return (
        resolve_state_directory()
        / f"instructions-skill-loaded-{sanitized_session_id}.marker"
    )
