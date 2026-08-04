from __future__ import annotations

import re
import sys
from pathlib import Path

_MODULE_DIRECTORY = Path(__file__).resolve().parent
for _shared_module_candidate_directory in [_MODULE_DIRECTORY] + [
    ancestor / "common" for ancestor in _MODULE_DIRECTORY.parents
]:
    _shared_module_candidate_path = str(_shared_module_candidate_directory)
    if (
        _shared_module_candidate_directory.is_dir()
        and _shared_module_candidate_path not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_path)

from hook_dispatch import HandlerResult  # noqa: E402
from prohibited_command_patterns import PROHIBITED_PATTERNS_BY_TOOL  # noqa: E402


def extract_inspectable_text(tool_name: str, tool_input: dict) -> str:
    if tool_name == "Bash":
        return tool_input.get("command", "") or ""
    if tool_name == "apply_patch":
        if isinstance(tool_input, str):
            return tool_input
        if isinstance(tool_input, dict):
            return tool_input.get("patch_text", "") or ""
        return ""
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
    inspection_texts = (inspectable_text,)
    if tool_name == "Bash":
        shell_quote_normalized_text = (
            inspectable_text.replace("\\\n", "")
            .replace("\\", "")
            .replace("'", "")
            .replace('"', "")
        )
        inspection_texts += (
            shell_quote_normalized_text,
            shell_quote_normalized_text.replace("$", ""),
        )

    for rule in patterns_for_this_tool:
        pattern, reason = rule[0], rule[1]
        override_sentinel = rule[2] if len(rule) > 2 else None
        if not any(
            re.search(pattern, candidate_text, re.IGNORECASE)
            for candidate_text in inspection_texts
        ):
            continue
        if override_sentinel and override_sentinel in inspectable_text:
            continue
        return pattern, reason
    return None


def handle(hook_input):
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {}) or {}

    inspectable_text = extract_inspectable_text(tool_name, tool_input)
    violation = find_first_violation(tool_name, inspectable_text)

    if violation is None:
        return None

    _pattern, reason = violation
    block_message = (
        f"BLOCKED ({tool_name}): {reason}\nOffending input: {inspectable_text.strip()}"
    )
    return HandlerResult(
        decision="deny", reason=block_message, system_message=block_message
    )
