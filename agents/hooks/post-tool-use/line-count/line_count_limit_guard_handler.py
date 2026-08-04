from __future__ import annotations

import sys
from pathlib import Path

_MODULE_DIRECTORY = Path(__file__).resolve().parent
for _shared_module_candidate_directory in (
    _MODULE_DIRECTORY,
    _MODULE_DIRECTORY.parent.parent / "common",
):
    _shared_module_candidate_path = str(_shared_module_candidate_directory)
    if (
        _shared_module_candidate_directory.is_dir()
        and _shared_module_candidate_path not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_path)

from changed_file_paths import collect_changed_file_paths  # noqa: E402
from hook_dispatch import HandlerResult  # noqa: E402
from line_count_policy import (  # noqa: E402
    LINE_COUNT_BLOCKING_THRESHOLD,
    line_count_when_code_file_exceeds_blocking_threshold,
)

APPLICABLE_TOOL_NAMES = frozenset(
    {"Write", "Edit", "MultiEdit", "NotebookEdit", "apply_patch"}
)

BLOCK_MESSAGE_REFERENCE_FILE_PATH = "~/.claude/hooks/line-count-block-message.md"


def blocking_result(target_file_path: str, line_count: int):
    reason = (
        f"File '{target_file_path}' is {line_count} lines, over the "
        f"{LINE_COUNT_BLOCKING_THRESHOLD}-line hard limit. Split it into modules "
        f"with single responsibilities, then read "
        f"{BLOCK_MESSAGE_REFERENCE_FILE_PATH} for where the pieces belong."
    )
    system_message = (
        f"BLOCKED: {target_file_path} has {line_count} lines "
        f"(> {LINE_COUNT_BLOCKING_THRESHOLD})."
    )
    return HandlerResult(decision="block", reason=reason, system_message=system_message)


def handle(hook_input: dict):
    tool_name = hook_input.get("tool_name", "")
    if tool_name not in APPLICABLE_TOOL_NAMES:
        return None

    for target_file_path in collect_changed_file_paths(hook_input):
        line_count = line_count_when_code_file_exceeds_blocking_threshold(
            target_file_path
        )
        if line_count is not None:
            return blocking_result(target_file_path, line_count)
    return None
