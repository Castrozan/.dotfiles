#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

_MODULE_DIRECTORY = Path(__file__).resolve().parent
for _shared_module_candidate_directory in [_MODULE_DIRECTORY] + [
    ancestor / "common" for ancestor in _MODULE_DIRECTORY.parents
]:
    _shared_module_candidate_path = str(_shared_module_candidate_directory)
    if (
        _shared_module_candidate_directory.is_dir()
        and _shared_module_candidate_path not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_path)

import prohibited_command_guard_handler  # noqa: E402
from pre_tool_use_block import deny_pre_tool_use_call  # noqa: E402


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    result = prohibited_command_guard_handler.handle(data)
    if result is None or result.decision != "deny":
        sys.exit(0)

    deny_pre_tool_use_call(result.reason)


if __name__ == "__main__":
    main()
