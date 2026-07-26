from __future__ import annotations

import sys
from pathlib import Path

_MODULE_DIRECTORY = Path(__file__).resolve().parent
for _shared_module_candidate_directory in (
    _MODULE_DIRECTORY,
    _MODULE_DIRECTORY.parent.parent / "common",
):
    _shared_module_candidate_path = str(_shared_module_candidate_directory)
    if (
        _shared_module_candidate_directory.is_dir()
        and _shared_module_candidate_path not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_path)

import instructions_skill_marker  # noqa: E402


def invoked_skill_name(tool_input):
    return (tool_input.get("skill", "") or "").strip().lower()


def is_instructions_skill(skill_name):
    return skill_name == "instructions" or skill_name.endswith(":instructions")


def record_instructions_skill_loaded(session_id):
    marker_path = instructions_skill_marker.instructions_skill_loaded_marker_path(
        session_id
    )
    try:
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text("loaded")
    except OSError:
        pass


def handle(hook_input: dict):
    tool_input = hook_input.get("tool_input", {})
    if not is_instructions_skill(invoked_skill_name(tool_input)):
        return None
    record_instructions_skill_loaded(hook_input.get("session_id", ""))
    return None
