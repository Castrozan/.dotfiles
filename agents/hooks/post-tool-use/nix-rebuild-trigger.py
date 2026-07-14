#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path

_MODULE_DIRECTORY = Path(__file__).resolve().parent
for _shared_module_candidate_directory in (
    _MODULE_DIRECTORY,
    _MODULE_DIRECTORY.parent / "common",
):
    _shared_module_candidate_path = str(_shared_module_candidate_directory)
    if (
        _shared_module_candidate_directory.is_dir()
        and _shared_module_candidate_path not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_path)

from changed_file_paths import collect_changed_file_paths  # noqa: E402

NIX_FILE_EXTENSIONS = [
    ".nix",
]


def has_nix_file_extension(path: str) -> bool:
    if not path:
        return False

    for extension in NIX_FILE_EXTENSIONS:
        if path.endswith(extension):
            return True

    return False


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    changed_nix_files = [
        path
        for path in collect_changed_file_paths(data)
        if has_nix_file_extension(path)
    ]

    if not changed_nix_files:
        sys.exit(0)

    changed_nix_file_names = ", ".join(
        sorted({os.path.basename(path) for path in changed_nix_files})
    )
    mandatory_rebuild_message = (
        f"MANDATORY: {changed_nix_file_names} changed. "
        "You MUST stage, commit, and run the rebuild "
        "before responding to the user. "
        "Do not skip. Untested nix changes are not changes."
    )
    output = {
        "continue": True,
        "systemMessage": mandatory_rebuild_message,
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": mandatory_rebuild_message,
        },
    }
    print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
