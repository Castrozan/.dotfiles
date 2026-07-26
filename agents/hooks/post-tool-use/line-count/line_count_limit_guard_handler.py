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

from hook_dispatch import HandlerResult  # noqa: E402
from line_count_policy import (  # noqa: E402
    LINE_COUNT_BLOCKING_THRESHOLD,
    line_count_when_code_file_exceeds_blocking_threshold,
)

APPLICABLE_TOOL_NAMES = frozenset({"Write", "Edit", "MultiEdit", "NotebookEdit"})

BLOCK_MESSAGE_FILE_PATH = _MODULE_DIRECTORY / "line-count-block-message.md"
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


def handle(hook_input: dict):
    tool_name = hook_input.get("tool_name", "")
    if tool_name not in APPLICABLE_TOOL_NAMES:
        return None

    tool_input = hook_input.get("tool_input", {}) or {}
    target_file_path = extract_target_file_path_from_tool_input(tool_name, tool_input)
    if not target_file_path:
        return None

    line_count = line_count_when_code_file_exceeds_blocking_threshold(target_file_path)
    if line_count is None:
        return None

    reason = (
        f"File '{target_file_path}' is {line_count} lines, exceeding the "
        f"{LINE_COUNT_BLOCKING_THRESHOLD}-line hard limit. "
        f"{read_block_message_guidance()}"
    )
    system_message = (
        f"BLOCKED: {target_file_path} has {line_count} lines "
        f"(> {LINE_COUNT_BLOCKING_THRESHOLD})."
    )
    return HandlerResult(decision="block", reason=reason, system_message=system_message)
