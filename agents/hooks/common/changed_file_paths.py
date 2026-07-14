from __future__ import annotations

import json
import os
import re

_APPLY_PATCH_FILE_MARKER_PATTERN = re.compile(
    r"^\*\*\* (?:Add|Update|Delete) File: ([^\"\n]+)", re.MULTILINE
)
_APPLY_PATCH_MOVE_MARKER_PATTERN = re.compile(
    r"^\*\*\* Move to: ([^\"\n]+)", re.MULTILINE
)
_APPLY_PATCH_ADDED_LINE_PATTERN = re.compile(r"^\+(.*)$", re.MULTILINE)


def _directly_reported_edited_path(tool_input: object) -> str:
    if not isinstance(tool_input, dict):
        return ""
    return str(tool_input.get("file_path") or tool_input.get("path") or "")


def _serialized_tool_input(hook_input: dict) -> str:
    tool_input = hook_input.get("tool_input")
    if tool_input is None:
        return ""
    serialized_tool_input = (
        tool_input if isinstance(tool_input, str) else json.dumps(tool_input)
    )
    return serialized_tool_input.replace("\\n", "\n")


def _paths_declared_in_apply_patch_markers(hook_input: dict) -> list[str]:
    serialized_payload = _serialized_tool_input(hook_input)
    marker_matches = _APPLY_PATCH_FILE_MARKER_PATTERN.findall(serialized_payload)
    marker_matches += _APPLY_PATCH_MOVE_MARKER_PATTERN.findall(serialized_payload)
    return [
        marker_match.strip().strip('"').rstrip("\\").strip()
        for marker_match in marker_matches
    ]


def apply_patch_added_content(hook_input: dict) -> str:
    serialized_payload = _serialized_tool_input(hook_input)
    return "\n".join(_APPLY_PATCH_ADDED_LINE_PATTERN.findall(serialized_payload))


def collect_changed_file_paths(hook_input: dict) -> list[str]:
    tool_input = hook_input.get("tool_input")
    unresolved_paths = []
    directly_reported_path = _directly_reported_edited_path(tool_input)
    if directly_reported_path:
        unresolved_paths.append(directly_reported_path)
    else:
        unresolved_paths.extend(_paths_declared_in_apply_patch_markers(hook_input))

    working_directory = hook_input.get("cwd") or os.getcwd()
    resolved_paths = []
    already_resolved = set()
    for unresolved_path in unresolved_paths:
        if not unresolved_path:
            continue
        absolute_path = (
            unresolved_path
            if os.path.isabs(unresolved_path)
            else os.path.join(working_directory, unresolved_path)
        )
        normalized_path = os.path.normpath(absolute_path)
        if normalized_path not in already_resolved:
            already_resolved.add(normalized_path)
            resolved_paths.append(normalized_path)
    return resolved_paths
