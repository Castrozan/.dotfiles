import os
import re

STATE_DIRECTORY_OVERRIDE_ENVIRONMENT_VARIABLE = (
    "AGENT_SKILL_LOADED_MARKER_STATE_DIRECTORY"
)

DEFAULT_STATE_DIRECTORY = "/tmp"


def resolve_state_directory():
    return (
        os.environ.get(STATE_DIRECTORY_OVERRIDE_ENVIRONMENT_VARIABLE)
        or DEFAULT_STATE_DIRECTORY
    )


def _sanitized_component(value):
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", value or "unknown")


def skill_loaded_marker_path(skill_name, session_id):
    return os.path.join(
        resolve_state_directory(),
        f"{_sanitized_component(skill_name)}-skill-loaded-"
        f"{_sanitized_component(session_id)}.marker",
    )


def record_skill_loaded(skill_name, session_id):
    marker_path = skill_loaded_marker_path(skill_name, session_id)
    try:
        os.makedirs(os.path.dirname(marker_path), exist_ok=True)
        with open(marker_path, "w") as marker_file:
            marker_file.write("loaded")
    except OSError:
        pass


def has_skill_loaded(skill_name, session_id):
    return os.path.exists(skill_loaded_marker_path(skill_name, session_id))
