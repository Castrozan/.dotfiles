#!/usr/bin/env python3
"""Run available linters after file edits and report issues to the model.

Exit codes:
  0 - silent pass-through (no issues, no linters available, or file skipped)
  1 - invalid input JSON
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lint_on_edit_linter_table import LINTERS_BY_FILE_EXTENSION
from lint_on_edit_runner import (
    is_linter_executable_available_in_path,
    run_linter_on_file,
)

MAX_FILE_SIZE_BYTES_FOR_LINTING = 500 * 1024
MAX_ISSUES_PER_LINTER = 3
MAX_ISSUES_DISPLAYED = 5


def read_hook_input_or_exit() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)


def is_file_eligible_for_linting(file_path: str) -> bool:
    if not file_path or not os.path.exists(file_path):
        return False
    try:
        if os.path.getsize(file_path) > MAX_FILE_SIZE_BYTES_FOR_LINTING:
            return False
    except OSError:
        return False
    return True


def collect_issues_from_first_failing_linter(
    file_path: str, linters: list[dict]
) -> tuple[list[str], list[str]]:
    collected_issues: list[str] = []
    linters_actually_run: list[str] = []
    for linter in linters:
        if not is_linter_executable_available_in_path(linter["cmd"]):
            continue
        linters_actually_run.append(linter["name"])
        issues = run_linter_on_file(file_path, linter)
        if issues:
            collected_issues.extend(issues[:MAX_ISSUES_PER_LINTER])
            break
    return collected_issues, linters_actually_run


def format_issues_for_system_message(issues: list[str]) -> str:
    displayed = issues[:MAX_ISSUES_DISPLAYED]
    issue_text = "\n".join(f"  - {issue}" for issue in displayed)
    if len(issues) > MAX_ISSUES_DISPLAYED:
        issue_text += f"\n  ... and {len(issues) - MAX_ISSUES_DISPLAYED} more"
    return issue_text


def main() -> None:
    hook_input = read_hook_input_or_exit()
    file_path = hook_input.get("tool_input", {}).get("file_path", "")

    if not is_file_eligible_for_linting(file_path):
        sys.exit(0)

    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()

    if file_extension not in LINTERS_BY_FILE_EXTENSION:
        sys.exit(0)

    issues, linters_run = collect_issues_from_first_failing_linter(
        file_path, LINTERS_BY_FILE_EXTENSION[file_extension]
    )

    if not linters_run:
        sys.exit(0)

    if issues:
        output = {
            "continue": True,
            "systemMessage": (
                f"LINT ISSUES ({linters_run[0]}):\n"
                f"{format_issues_for_system_message(issues)}\n"
                "These lint issues are CI blockers; fix before pushing."
            ),
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
