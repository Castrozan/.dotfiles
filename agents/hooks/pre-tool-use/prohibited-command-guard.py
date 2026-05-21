#!/usr/bin/env python3
"""Block tool invocations that violate documented policies.

Exit codes:
  0 - Allow the tool call to proceed.
  2 - BLOCK the tool call (policy violation).
"""

from __future__ import annotations

import json
import re
import sys

COMMAND_BOUNDARY_PREFIX = r"(?:^|[;&|`(]\s*)"

PROHIBITED_BASH_COMMAND_PATTERNS = [
    (
        rf"{COMMAND_BOUNDARY_PREFIX}git\s+add\s+(-A|--all|\.)(\s|$)",
        "git add -A/--all/. is prohibited; stage specific files (parallel work risk).",
    ),
    (
        rf"{COMMAND_BOUNDARY_PREFIX}(?:git|gh\s+repo)\s+clone\s+\S*castrozan[/-]?\.?dotfiles",
        "Cloning castrozan/.dotfiles is prohibited; use 'gh api' for remote access.",
    ),
    (
        rf"{COMMAND_BOUNDARY_PREFIX}direnv\s+(allow|hook|exec|reload|status|edit|deny|block|prune|version)\b",
        "direnv is prohibited; use 'devenv shell' or 'devenv shell -- command'.",
    ),
]

PROHIBITED_FILE_PATH_PATTERNS = [
    (
        r"(?:^|/)castrozan/\.?dotfiles(?:/|$)",
        "Writing under castrozan/.dotfiles is prohibited; repo must not live on disk.",
    ),
]

PROHIBITED_PATTERNS_BY_TOOL = {
    "Bash": PROHIBITED_BASH_COMMAND_PATTERNS,
    "Write": PROHIBITED_FILE_PATH_PATTERNS,
    "Edit": PROHIBITED_FILE_PATH_PATTERNS,
    "NotebookEdit": PROHIBITED_FILE_PATH_PATTERNS,
}


def extract_inspectable_text(tool_name: str, tool_input: dict) -> str:
    if tool_name == "Bash":
        return tool_input.get("command", "") or ""
    if tool_name in ("Write", "Edit"):
        return tool_input.get("file_path", "") or ""
    if tool_name == "NotebookEdit":
        return (
            tool_input.get("notebook_path", "") or tool_input.get("file_path", "") or ""
        )
    return ""


def find_first_violation(tool_name: str, inspectable_text: str):
    if not inspectable_text:
        return None

    patterns_for_this_tool = PROHIBITED_PATTERNS_BY_TOOL.get(tool_name, [])

    for pattern, reason in patterns_for_this_tool:
        if re.search(pattern, inspectable_text, re.IGNORECASE):
            return pattern, reason
    return None


def emit_block_and_exit(reason: str, tool_name: str, inspectable_text: str) -> None:
    output = {
        "continue": False,
        "systemMessage": (
            f"BLOCKED ({tool_name}): {reason}\n"
            f"Offending input: {inspectable_text.strip()}"
        ),
    }
    print(json.dumps(output))
    sys.exit(2)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}

    inspectable_text = extract_inspectable_text(tool_name, tool_input)
    violation = find_first_violation(tool_name, inspectable_text)

    if violation is None:
        sys.exit(0)

    _pattern, reason = violation
    emit_block_and_exit(reason, tool_name, inspectable_text)


if __name__ == "__main__":
    main()
