#!/usr/bin/env python3

import json
import sys
from pathlib import Path


def load_instructions_skill_marker_module():
    hook_script_directory = Path(__file__).resolve().parent
    shared_common_hook_modules_directory = (
        hook_script_directory.parent.parent / "common"
    )
    for candidate_directory in (
        hook_script_directory,
        shared_common_hook_modules_directory,
    ):
        candidate_directory_string = str(candidate_directory)
        if candidate_directory.is_dir() and candidate_directory_string not in sys.path:
            sys.path.insert(0, candidate_directory_string)
    import instructions_skill_marker

    return instructions_skill_marker


def invoked_skill_name(tool_input):
    return (tool_input.get("skill", "") or "").strip().lower()


def is_instructions_skill(skill_name):
    return skill_name == "instructions" or skill_name.endswith(":instructions")


def record_instructions_skill_loaded(session_id):
    instructions_skill_marker = load_instructions_skill_marker_module()
    marker_path = instructions_skill_marker.instructions_skill_loaded_marker_path(
        session_id
    )
    try:
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text("loaded")
    except OSError:
        pass


def main():
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_input = hook_input.get("tool_input", {})
    if not is_instructions_skill(invoked_skill_name(tool_input)):
        sys.exit(0)

    record_instructions_skill_loaded(hook_input.get("session_id", ""))
    sys.exit(0)


if __name__ == "__main__":
    main()
