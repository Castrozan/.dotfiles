#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lint_ledger import append_edited_source_file  # noqa: E402
from linter_table_by_extension import LINTERS_BY_FILE_EXTENSION  # noqa: E402


def read_hook_input_or_exit() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)


def main() -> None:
    hook_input = read_hook_input_or_exit()
    file_path = hook_input.get("tool_input", {}).get("file_path", "")
    session_id = hook_input.get("session_id", "")

    if not file_path or not os.path.exists(file_path):
        sys.exit(0)

    _, file_extension = os.path.splitext(file_path)
    if file_extension.lower() not in LINTERS_BY_FILE_EXTENSION:
        sys.exit(0)

    append_edited_source_file(session_id, os.path.abspath(file_path))
    sys.exit(0)


if __name__ == "__main__":
    main()
