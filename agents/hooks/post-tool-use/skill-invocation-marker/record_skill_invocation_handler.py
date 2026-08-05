from __future__ import annotations

import os
import sys

_MODULE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
for _shared_module_candidate_directory in (
    _MODULE_DIRECTORY,
    os.path.join(os.path.dirname(os.path.dirname(_MODULE_DIRECTORY)), "common"),
):
    if (
        os.path.isdir(_shared_module_candidate_directory)
        and _shared_module_candidate_directory not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_directory)

import skill_loaded_marker  # noqa: E402


def invoked_skill_name(tool_input):
    return (tool_input.get("skill", "") or "").strip().lower()


def canonical_skill_name(skill_name):
    return skill_name.rsplit(":", 1)[-1].strip()


def handle(hook_input: dict):
    tool_input = hook_input.get("tool_input", {})
    skill_name = invoked_skill_name(tool_input)
    if not skill_name:
        return None
    skill_loaded_marker.record_skill_loaded(
        canonical_skill_name(skill_name), hook_input.get("session_id", "")
    )
    return None
