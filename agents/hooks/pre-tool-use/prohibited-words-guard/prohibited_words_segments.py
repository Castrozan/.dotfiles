from __future__ import annotations

import re
from pathlib import Path

from changed_file_paths import apply_patch_added_content, collect_changed_file_paths

PRIVATE_REPOSITORY_PATH_SEGMENT = "private-config"

PUBLISHING_COMMAND_PATTERNS = [
    r"\bgit\b[^\n|;&]*\bcommit\b",
    r"\bgit\b[^\n|;&]*\btag\b[^\n|;&]*-(?:m|a|F)\b",
    r"\bgh\b[^\n|;&]*\b(?:pr|issue|release)\b[^\n|;&]*\b(?:create|edit)\b",
    r"\bglab\b[^\n|;&]*\b(?:mr|issue)\b[^\n|;&]*\b(?:create|update|edit)\b",
]


def path_is_within_private_repository(file_path: str) -> bool:
    if not file_path:
        return False
    return PRIVATE_REPOSITORY_PATH_SEGMENT in Path(file_path).parts


def command_targets_private_repository(
    command: str, current_working_directory: str
) -> bool:
    return (
        PRIVATE_REPOSITORY_PATH_SEGMENT in command
        or PRIVATE_REPOSITORY_PATH_SEGMENT in (current_working_directory or "")
    )


def command_publishes_text_to_shared_history(command: str) -> bool:
    return any(
        re.search(pattern, command, re.IGNORECASE)
        for pattern in PUBLISHING_COMMAND_PATTERNS
    )


def collect_written_content_segments(
    tool_name: str, tool_input: dict
) -> list[tuple[str, str]]:
    if tool_name == "Write":
        return [("file contents", tool_input.get("content", "") or "")]
    if tool_name == "Edit":
        return [("file contents", tool_input.get("new_string", "") or "")]
    if tool_name == "NotebookEdit":
        return [("file contents", tool_input.get("new_source", "") or "")]
    if tool_name == "MultiEdit":
        edits = tool_input.get("edits", []) or []
        return [
            ("file contents", edit.get("new_string", "") or "")
            for edit in edits
            if isinstance(edit, dict)
        ]
    return []


def collect_apply_patch_segments(
    tool_input: dict, current_working_directory: str
) -> list[tuple[str, str]]:
    payload_view = {"tool_input": tool_input, "cwd": current_working_directory}
    public_target_paths = [
        path
        for path in collect_changed_file_paths(payload_view)
        if not path_is_within_private_repository(path)
    ]
    if not public_target_paths:
        return []
    segments = [("file name", path) for path in public_target_paths]
    added_content = apply_patch_added_content(payload_view)
    if added_content:
        segments.append(("file contents", added_content))
    return segments


def collect_segments_to_inspect(
    tool_name: str, tool_input: dict, current_working_directory: str
) -> list[tuple[str, str]]:
    if tool_name == "Bash":
        command = tool_input.get("command", "") or ""
        if not command_publishes_text_to_shared_history(command):
            return []
        if command_targets_private_repository(command, current_working_directory):
            return []
        return [("commit or publish command", command)]

    if tool_name == "apply_patch":
        return collect_apply_patch_segments(tool_input, current_working_directory)

    if tool_name in ("Write", "Edit", "NotebookEdit", "MultiEdit"):
        file_path = (
            tool_input.get("file_path", "") or tool_input.get("notebook_path", "") or ""
        )
        if path_is_within_private_repository(file_path):
            return []
        segments = [("file name", file_path)]
        segments.extend(collect_written_content_segments(tool_name, tool_input))
        return segments

    return []
