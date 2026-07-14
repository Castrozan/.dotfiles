#!/usr/bin/env python3
from __future__ import annotations

import json
import os
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

from codex_tool_payload import normalize_codex_tool_payload  # noqa: E402
from pre_tool_use_block import deny_pre_tool_use_call  # noqa: E402
from prohibited_words_segments import collect_segments_to_inspect  # noqa: E402

DEFAULT_PROHIBITED_WORDS_FILE = (
    Path.home() / ".dotfiles" / "private-config" / "claude" / "prohibited-words.txt"
)


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
    deny_pre_tool_use_call(
        f"BLOCKED ({tool_name}): the word '{word}' must not appear in {label} "
        f"outside private repositories. Move it into private-config, or remove it."
    )


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

    data = normalize_codex_tool_payload(data)

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
