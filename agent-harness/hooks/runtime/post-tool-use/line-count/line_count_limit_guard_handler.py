from __future__ import annotations

import os
import sys

_MODULE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
for _shared_module_candidate_directory in (
    _MODULE_DIRECTORY,
    os.path.join(os.path.dirname(os.path.dirname(_MODULE_DIRECTORY)), "common"),
):
    if (
        os.path.isdir(_shared_module_candidate_directory)
        and _shared_module_candidate_directory not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_directory)

from changed_file_paths import collect_changed_file_paths  # noqa: E402
from hook_dispatch import HandlerResult  # noqa: E402
from line_count_baseline import allowed_line_count_for_file  # noqa: E402
from line_count_policy import (  # noqa: E402
    LINE_COUNT_BLOCKING_THRESHOLD,
    LineCountViolation,
    line_count_violation,
)

APPLICABLE_TOOL_NAMES = frozenset(
    {"Write", "Edit", "MultiEdit", "NotebookEdit", "apply_patch"}
)

BLOCK_MESSAGE_REFERENCE_FILE_PATH = "~/.claude/hooks/line-count-block-message.md"


def blocking_result(violation: LineCountViolation):
    if violation.allowed_line_count == LINE_COUNT_BLOCKING_THRESHOLD:
        ceiling_description = f"the {LINE_COUNT_BLOCKING_THRESHOLD}-line hard limit"
    else:
        ceiling_description = (
            f"its {violation.allowed_line_count}-line grandfathered ceiling"
        )
    reason = (
        f"File '{violation.file_path}' is {violation.line_count} lines, over "
        f"{ceiling_description}. Split it into modules with single "
        f"responsibilities, then read {BLOCK_MESSAGE_REFERENCE_FILE_PATH} for "
        f"where the pieces belong."
    )
    system_message = (
        f"BLOCKED: {violation.file_path} has {violation.line_count} lines "
        f"(> {violation.allowed_line_count})."
    )
    return HandlerResult(decision="block", reason=reason, system_message=system_message)


def handle(hook_input: dict):
    tool_name = hook_input.get("tool_name", "")
    if tool_name not in APPLICABLE_TOOL_NAMES:
        return None

    for target_file_path in collect_changed_file_paths(hook_input):
        violation = line_count_violation(
            target_file_path, allowed_line_count_for_file(target_file_path)
        )
        if violation is not None:
            return blocking_result(violation)
    return None
