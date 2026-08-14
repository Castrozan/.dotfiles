from __future__ import annotations

import os
import re
import sys

_MODULE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
_ANCESTOR_DIRECTORY = _MODULE_DIRECTORY
_SHARED_MODULE_CANDIDATE_DIRECTORIES = [_MODULE_DIRECTORY]
while _ANCESTOR_DIRECTORY != os.path.dirname(_ANCESTOR_DIRECTORY):
    _ANCESTOR_DIRECTORY = os.path.dirname(_ANCESTOR_DIRECTORY)
    _SHARED_MODULE_CANDIDATE_DIRECTORIES.append(
        os.path.join(_ANCESTOR_DIRECTORY, "common")
    )
for _shared_module_candidate_directory in _SHARED_MODULE_CANDIDATE_DIRECTORIES:
    if (
        os.path.isdir(_shared_module_candidate_directory)
        and _shared_module_candidate_directory not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_directory)

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


def pattern_matches_outside_read_only_inspection(pattern: str, candidate_text: str):
    from shell_read_only_inspection_command import (
        offset_lies_in_text_the_shell_never_runs,
    )

    for match in re.finditer(pattern, candidate_text, re.IGNORECASE):
        if match.start() == match.end():
            return True
        if not offset_lies_in_text_the_shell_never_runs(candidate_text, match.start()):
            return True
    return False


def pattern_matches_executed_command_group(
    pattern: str, candidate_text: str, command_group: str
):
    from shell_command_segment_scanning import (
        offset_is_inside_command_substitution,
        quote_state_by_offset,
    )
    from shell_heredoc_body import offset_lies_in_inert_heredoc_body

    quote_states = quote_state_by_offset(candidate_text)
    for match in re.finditer(pattern, candidate_text, re.IGNORECASE):
        command_offset = match.start(command_group)
        if offset_lies_in_inert_heredoc_body(candidate_text, command_offset):
            continue
        if not quote_states[command_offset] or offset_is_inside_command_substitution(
            candidate_text, command_offset
        ):
            return True
    return False


def find_first_violation(tool_name: str, inspectable_text: str):
    if not inspectable_text:
        return None

    patterns_for_this_tool = PROHIBITED_PATTERNS_BY_TOOL.get(tool_name, [])
    inspection_texts_most_faithful_first = (inspectable_text,)
    if tool_name == "Bash":
        shell_quote_normalized_text = (
            inspectable_text.replace("\\\n", "")
            .replace("\\", "")
            .replace("'", "")
            .replace('"', "")
        )
        inspection_texts_most_faithful_first += (
            shell_quote_normalized_text,
            shell_quote_normalized_text.replace("$", ""),
        )

    for rule in patterns_for_this_tool:
        pattern, reason = rule[0], rule[1]
        override_sentinel = rule[2] if len(rule) > 2 else None
        executed_command_group = rule[3] if len(rule) > 3 else None
        matching_texts_most_faithful_first = [
            candidate_text
            for candidate_text in inspection_texts_most_faithful_first
            if re.search(pattern, candidate_text, re.IGNORECASE)
        ]
        if not matching_texts_most_faithful_first:
            continue
        if tool_name == "Bash":
            if executed_command_group:
                if not pattern_matches_executed_command_group(
                    pattern, inspectable_text, executed_command_group
                ):
                    continue
            elif not pattern_matches_outside_read_only_inspection(
                pattern, matching_texts_most_faithful_first[0]
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
