#!/usr/bin/env python3
"""Enforce the file-length hard limit on code files after Write/Edit.

The threshold comes from line_count_policy.py. Over it, emits decision="block"
so the model gets next-turn feedback; at or under it, stays silent.

Exit codes:
  0 - always (silent pass-through when the file is within the limit)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from line_count_policy import (  # noqa: E402
    LINE_COUNT_BLOCKING_THRESHOLD,
    line_count_when_code_file_exceeds_blocking_threshold,
)

APPLICABLE_TOOL_NAMES = frozenset({"Write", "Edit", "MultiEdit", "NotebookEdit"})

BLOCK_MESSAGE_FILE_PATH = Path(__file__).parent / "line-count-block-message.md"
BLOCK_MESSAGE_FALLBACK = (
    "Split it into smaller modules with single responsibilities before continuing."
)


def extract_target_file_path_from_tool_input(tool_name: str, tool_input: dict) -> str:
    if tool_name == "NotebookEdit":
        return tool_input.get("notebook_path", "") or ""
    return tool_input.get("file_path", "") or ""


def read_block_message_guidance() -> str:
    try:
        return BLOCK_MESSAGE_FILE_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        return BLOCK_MESSAGE_FALLBACK


def build_blocking_payload(file_path: str, line_count: int) -> dict:
    reason = (
        f"File '{file_path}' is {line_count} lines, exceeding the "
        f"{LINE_COUNT_BLOCKING_THRESHOLD}-line hard limit. "
        f"{read_block_message_guidance()}"
    )
    return {
        "decision": "block",
        "reason": reason,
        "systemMessage": (
            f"BLOCKED: {file_path} has {line_count} lines "
            f"(> {LINE_COUNT_BLOCKING_THRESHOLD})."
        ),
    }


def main() -> None:
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    if tool_name not in APPLICABLE_TOOL_NAMES:
        sys.exit(0)

    tool_input = hook_input.get("tool_input", {}) or {}
    target_file_path = extract_target_file_path_from_tool_input(tool_name, tool_input)
    if not target_file_path:
        sys.exit(0)

    line_count = line_count_when_code_file_exceeds_blocking_threshold(target_file_path)
    if line_count is None:
        sys.exit(0)

    print(json.dumps(build_blocking_payload(target_file_path, line_count)))
    sys.exit(0)


if __name__ == "__main__":
    main()
