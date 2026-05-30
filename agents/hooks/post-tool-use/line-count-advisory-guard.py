#!/usr/bin/env python3
"""Enforce file-length guidelines on code files after Write/Edit.

Thresholds (line counts) come from line_count_policy.py. Above the blocking
threshold emits decision="block" so the model gets next-turn feedback.

Exit codes:
  0 - silent pass-through (no advisory, or non-applicable file)
  1 - invalid input JSON
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from line_count_policy import (
    LINE_COUNT_ADVISORY_THRESHOLD,
    LINE_COUNT_BLOCKING_THRESHOLD,
    LINE_COUNT_WARNING_THRESHOLD,
    SEVERITY_ADVISORY,
    SEVERITY_BLOCKING,
    SEVERITY_WARNING,
    evaluate_code_file_line_count,
)

APPLICABLE_TOOL_NAMES = frozenset({"Write", "Edit", "MultiEdit", "NotebookEdit"})


def extract_target_file_path_from_tool_input(tool_name: str, tool_input: dict) -> str:
    if tool_name == "NotebookEdit":
        return tool_input.get("notebook_path", "") or ""
    return tool_input.get("file_path", "") or ""


def build_blocking_payload(file_path: str, line_count: int) -> dict:
    reason = (
        f"File '{file_path}' is {line_count} lines, exceeding the "
        f"{LINE_COUNT_BLOCKING_THRESHOLD}-line hard limit. "
        "Split it into smaller modules with single responsibilities before continuing."
    )
    return {
        "decision": "block",
        "reason": reason,
        "systemMessage": (
            f"BLOCKED: {file_path} has {line_count} lines "
            f"(> {LINE_COUNT_BLOCKING_THRESHOLD})."
        ),
    }


def build_warning_payload(file_path: str, line_count: int) -> dict:
    return {
        "systemMessage": (
            f"WARNING: {file_path} is {line_count} lines "
            f"(> {LINE_COUNT_WARNING_THRESHOLD}). "
            "Split this file before it grows further."
        )
    }


def build_advisory_payload(file_path: str, line_count: int) -> dict:
    return {
        "systemMessage": (
            f"ADVISORY: {file_path} is {line_count} lines "
            f"(> {LINE_COUNT_ADVISORY_THRESHOLD}). "
            "Consider whether this file should be split."
        )
    }


def determine_payload_for_severity(
    file_path: str, line_count: int, severity: str
) -> dict | None:
    if severity == SEVERITY_BLOCKING:
        return build_blocking_payload(file_path, line_count)
    if severity == SEVERITY_WARNING:
        return build_warning_payload(file_path, line_count)
    if severity == SEVERITY_ADVISORY:
        return build_advisory_payload(file_path, line_count)
    return None


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

    evaluation = evaluate_code_file_line_count(target_file_path)
    if evaluation is None:
        sys.exit(0)

    line_count, severity = evaluation
    payload = determine_payload_for_severity(target_file_path, line_count, severity)
    if payload is None:
        sys.exit(0)

    print(json.dumps(payload))
    sys.exit(0)


if __name__ == "__main__":
    main()
