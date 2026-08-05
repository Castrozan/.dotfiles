from __future__ import annotations

import os
import sys

_MODULE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
for _shared_module_candidate_directory in (
    _MODULE_DIRECTORY,
    os.path.join(os.path.dirname(_MODULE_DIRECTORY), "common"),
):
    if (
        os.path.isdir(_shared_module_candidate_directory)
        and _shared_module_candidate_directory not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_directory)

from changed_file_paths import collect_changed_file_paths  # noqa: E402
from lint_ledger import append_edited_source_file  # noqa: E402
from linter_table_by_extension import LINTERS_BY_FILE_EXTENSION  # noqa: E402


def handle(hook_input: dict):
    session_id = hook_input.get("session_id", "")

    for file_path in collect_changed_file_paths(hook_input):
        if not os.path.exists(file_path):
            continue
        _, file_extension = os.path.splitext(file_path)
        if file_extension.lower() not in LINTERS_BY_FILE_EXTENSION:
            continue
        append_edited_source_file(session_id, os.path.abspath(file_path))

    return None
