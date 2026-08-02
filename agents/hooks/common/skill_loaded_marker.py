import os
import re
from pathlib import Path

STATE_DIRECTORY_OVERRIDE_ENVIRONMENT_VARIABLE = (
    "AGENT_SKILL_LOADED_MARKER_STATE_DIRECTORY"
)


def resolve_state_directory():
    override = os.environ.get(STATE_DIRECTORY_OVERRIDE_ENVIRONMENT_VARIABLE)
    if override:
        return Path(override)
    return Path("/tmp")


def _sanitized_component(value):
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", value or "unknown")


def skill_loaded_marker_path(skill_name, session_id):
    return (
        resolve_state_directory() / f"{_sanitized_component(skill_name)}-skill-loaded-"
        f"{_sanitized_component(session_id)}.marker"
    )


def record_skill_loaded(skill_name, session_id):
    marker_path = skill_loaded_marker_path(skill_name, session_id)
    try:
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text("loaded")
    except OSError:
        pass


def has_skill_loaded(skill_name, session_id):
    return skill_loaded_marker_path(skill_name, session_id).exists()
