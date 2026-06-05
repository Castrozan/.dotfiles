#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

DEFAULT_PROHIBITED_WORDS_FILE = (
    Path.home() / ".dotfiles" / "private-config" / "claude" / "prohibited-words.txt"
)

PRIVATE_REPOSITORY_PATH_SEGMENT = "private-config"

PUBLISHING_COMMAND_PATTERNS = [
    r"\bgit\b[^\n|;&]*\bcommit\b",
    r"\bgit\b[^\n|;&]*\btag\b[^\n|;&]*-(?:m|a|F)\b",
    r"\bgh\b[^\n|;&]*\b(?:pr|issue|release)\b[^\n|;&]*\b(?:create|edit)\b",
    r"\bglab\b[^\n|;&]*\b(?:mr|issue)\b[^\n|;&]*\b(?:create|update|edit)\b",
]


def resolve_prohibited_words_file() -> Path:
    override = os.environ.get("PROHIBITED_WORDS_FILE")
    if override:
        return Path(override)
    return DEFAULT_PROHIBITED_WORDS_FILE


def load_prohibited_words() -> list[str]:
    words_file = resolve_prohibited_words_file()
    try:
        raw_lines = words_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    words = []
    for line in raw_lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            words.append(stripped.lower())
    return words


def load_machine_allowed_words() -> set[str]:
    raw_allowed_words = os.environ.get("PROHIBITED_WORDS_ALLOWED", "")
    return {
        entry.strip().lower() for entry in raw_allowed_words.split(",") if entry.strip()
    }


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


def find_prohibited_word_in_segments(
    prohibited_words: list[str], segments: list[tuple[str, str]]
):
    for label, text in segments:
        lowered = text.lower()
        for word in prohibited_words:
            if word in lowered:
                return word, label
    return None


def emit_block_and_exit(tool_name: str, word: str, label: str) -> None:
    output = {
        "continue": False,
        "systemMessage": (
            f"BLOCKED ({tool_name}): the word '{word}' must not appear in {label} "
            f"outside private repositories. Move it into private-config, or remove it."
        ),
    }
    print(json.dumps(output))
    sys.exit(2)


def main() -> None:
    prohibited_words = load_prohibited_words()
    machine_allowed_words = load_machine_allowed_words()
    enforced_prohibited_words = [
        word for word in prohibited_words if word not in machine_allowed_words
    ]
    if not enforced_prohibited_words:
        sys.exit(0)

    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}
    current_working_directory = data.get("cwd", "") or ""

    segments = collect_segments_to_inspect(
        tool_name, tool_input, current_working_directory
    )
    violation = find_prohibited_word_in_segments(enforced_prohibited_words, segments)

    if violation is None:
        sys.exit(0)

    word, label = violation
    emit_block_and_exit(tool_name, word, label)


if __name__ == "__main__":
    main()
