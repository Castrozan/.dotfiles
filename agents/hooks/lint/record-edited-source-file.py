#!/usr/bin/env python3

from __future__ import annotations

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
from lint_ledger import append_edited_source_file  # noqa: E402
from linter_table_by_extension import LINTERS_BY_FILE_EXTENSION  # noqa: E402


def read_hook_input_or_exit() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)


def main() -> None:
    hook_input = read_hook_input_or_exit()
    session_id = hook_input.get("session_id", "")

    for file_path in collect_changed_file_paths(hook_input):
        if not os.path.exists(file_path):
            continue
        _, file_extension = os.path.splitext(file_path)
        if file_extension.lower() not in LINTERS_BY_FILE_EXTENSION:
            continue
        append_edited_source_file(session_id, os.path.abspath(file_path))

    sys.exit(0)


if __name__ == "__main__":
    main()
