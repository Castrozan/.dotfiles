#!/usr/bin/env python3

import json
import os
import subprocess
import sys

from lint_on_edit_linter_configurations import LINTER_COMMANDS_BY_FILE_EXTENSION

MAX_FILE_SIZE_BYTES = 500 * 1024
MAX_ISSUES_PER_LINTER = 3
MAX_DISPLAYED_ISSUES = 5


def is_linter_available_in_path(linter_command: list[str]) -> bool:
    try:
        subprocess.run(
            [linter_command[0], "--version"],
            capture_output=True,
            timeout=2,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        try:
            subprocess.run(
                [linter_command[0], "--help"],
                capture_output=True,
                timeout=2,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False


def collect_linter_issues_for_file(file_path: str, linter: dict) -> list[str]:
    command_with_file = linter["cmd"] + [file_path]

    try:
        result = subprocess.run(
            command_with_file,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.path.dirname(file_path) or ".",
        )
        combined_output = result.stdout + result.stderr
        parsed_issues = linter["parse"](combined_output)
        return [issue for issue in parsed_issues if issue.strip()]
    except subprocess.TimeoutExpired:
        return []
    except Exception:
        return []


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    file_path = data.get("tool_input", {}).get("file_path", "")

    if not file_path or not os.path.exists(file_path):
        sys.exit(0)

    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()

    if file_extension not in LINTER_COMMANDS_BY_FILE_EXTENSION:
        sys.exit(0)

    try:
        if os.path.getsize(file_path) > MAX_FILE_SIZE_BYTES:
            sys.exit(0)
    except OSError:
        sys.exit(0)

    all_issues = []
    successfully_run_linter_names = []

    for linter in LINTER_COMMANDS_BY_FILE_EXTENSION[file_extension]:
        if not is_linter_available_in_path(linter["cmd"]):
            continue

        successfully_run_linter_names.append(linter["name"])
        issues = collect_linter_issues_for_file(file_path, linter)
        if issues:
            all_issues.extend(issues[:MAX_ISSUES_PER_LINTER])
            break

    if not successfully_run_linter_names:
        sys.exit(0)

    if all_issues:
        displayed_issues = all_issues[:MAX_DISPLAYED_ISSUES]
        formatted_issue_text = "\n".join(f"  - {issue}" for issue in displayed_issues)
        if len(all_issues) > MAX_DISPLAYED_ISSUES:
            remaining = len(all_issues) - MAX_DISPLAYED_ISSUES
            formatted_issue_text += f"\n  ... and {remaining} more"

        linter_name = successfully_run_linter_names[0]
        output = {
            "continue": True,
            "systemMessage": (f"LINT ISSUES ({linter_name}):\n{formatted_issue_text}"),
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
