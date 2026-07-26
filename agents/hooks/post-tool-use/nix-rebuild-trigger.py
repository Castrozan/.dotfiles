#!/usr/bin/env python3

from __future__ import annotations

import json
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

from hook_dispatch import read_hook_input_or_exit  # noqa: E402
from nix_rebuild_trigger_handler import handle  # noqa: E402


def main() -> None:
    hook_input = read_hook_input_or_exit()
    result = handle(hook_input)
    if result is not None and (result.additional_context or result.system_message):
        payload: dict = {"continue": True}
        if result.system_message:
            payload["systemMessage"] = result.system_message
        if result.additional_context:
            payload["hookSpecificOutput"] = {
                "hookEventName": "PostToolUse",
                "additionalContext": result.additional_context,
            }
        print(json.dumps(payload))
    sys.exit(0)


if __name__ == "__main__":
    main()
