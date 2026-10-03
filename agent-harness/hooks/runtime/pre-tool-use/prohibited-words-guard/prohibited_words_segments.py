from __future__ import annotations

import os
import re

from changed_file_paths import apply_patch_added_content, collect_changed_file_paths

PRIVATE_REPOSITORY_PATH_SEGMENT = "private-configuration"
WRITTEN_FILE_CONTENTS_LABEL = "file contents"

PUBLISHING_COMMAND_PATTERNS = [
    r"\bgit\b[^\n|;&]*\bcommit\b",
    r"\bgit\b[^\n|;&]*\btag\b[^\n|;&]*-(?:m|a|F)\b",
    r"\bgh\b[^\n|;&]*\b(?:pr|issue|release)\b[^\n|;&]*\b(?:create|edit)\b",
    r"\bglab\b[^\n|;&]*\b(?:mr|issue)\b[^\n|;&]*\b(?:create|update|edit)\b",
]


def path_is_within_private_repository(file_path: str) -> bool:
    if not file_path:
        return False
    return PRIVATE_REPOSITORY_PATH_SEGMENT in file_path.split(os.sep)


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


def _collect_multi_edit_segments(tool_input):
    edits = tool_input.get("edits", []) or []
    return [
        (WRITTEN_FILE_CONTENTS_LABEL, edit.get("new_string", "") or "")
        for edit in edits
        if isinstance(edit, dict)
    ]


def _single_written_content_field(tool_name):
    if tool_name == "Write":
        return "content"
    if tool_name == "Edit":
        return "new_string"
    return "new_source"


def _single_written_content(tool_name, tool_input):
    content_field = _single_written_content_field(tool_name)
    return tool_input.get(content_field, "") or ""


def collect_written_content_segments(
    tool_name: str, tool_input: dict
) -> list[tuple[str, str]]:
    if tool_name == "MultiEdit":
        return _collect_multi_edit_segments(tool_input)
    if tool_name in ("Write", "Edit", "NotebookEdit"):
        return [
            (
                WRITTEN_FILE_CONTENTS_LABEL,
                _single_written_content(tool_name, tool_input),
            )
        ]
    return []


def _public_patch_target_paths(payload_view):
    return [
        path
        for path in collect_changed_file_paths(payload_view)
        if not path_is_within_private_repository(path)
    ]


def _append_patch_content_segment(segments, payload_view):
    added_content = apply_patch_added_content(payload_view)
    if added_content:
        segments.append((WRITTEN_FILE_CONTENTS_LABEL, added_content))


def collect_apply_patch_segments(
    tool_input: dict, current_working_directory: str
) -> list[tuple[str, str]]:
    payload_view = {"tool_input": tool_input, "cwd": current_working_directory}
    public_target_paths = _public_patch_target_paths(payload_view)
    if not public_target_paths:
        return []
    segments = [("file name", path) for path in public_target_paths]
    _append_patch_content_segment(segments, payload_view)
    return segments


def _bash_segments(tool_input, current_working_directory):
    command = tool_input.get("command", "") or ""
    if not command_publishes_text_to_shared_history(command):
        return []
    if command_targets_private_repository(command, current_working_directory):
        return []
    return [("commit or publish command", command)]


def _file_write_segments(tool_name, tool_input):
    file_path = (
        tool_input.get("file_path", "") or tool_input.get("notebook_path", "") or ""
    )
    if path_is_within_private_repository(file_path):
        return []
    segments = [("file name", file_path)]
    segments.extend(collect_written_content_segments(tool_name, tool_input))
    return segments


def collect_segments_to_inspect(
    tool_name: str, tool_input: dict, current_working_directory: str
) -> list[tuple[str, str]]:
    if tool_name == "Bash":
        return _bash_segments(tool_input, current_working_directory)
    if tool_name == "apply_patch":
        return collect_apply_patch_segments(tool_input, current_working_directory)
    if tool_name in ("Write", "Edit", "NotebookEdit", "MultiEdit"):
        return _file_write_segments(tool_name, tool_input)
    return []
