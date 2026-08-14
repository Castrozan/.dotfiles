from __future__ import annotations

import os
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
from prohibited_words_segments import collect_segments_to_inspect  # noqa: E402

DEFAULT_PROHIBITED_WORDS_FILE = os.path.join(
    os.path.expanduser("~"),
    ".dotfiles",
    "private-configuration",
    "agent-harness",
    "prohibited-words-guard",
    "prohibited-words.txt",
)


def resolve_prohibited_words_file() -> str:
    override = os.environ.get("PROHIBITED_WORDS_FILE")
    if override:
        return override
    return DEFAULT_PROHIBITED_WORDS_FILE


def load_prohibited_words() -> list[str]:
    words_file = resolve_prohibited_words_file()
    try:
        with open(words_file, encoding="utf-8") as words_file_handle:
            raw_lines = words_file_handle.read().splitlines()
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


def handle(hook_input):
    prohibited_words = load_prohibited_words()
    machine_allowed_words = load_machine_allowed_words()
    enforced_prohibited_words = [
        word for word in prohibited_words if word not in machine_allowed_words
    ]
    if not enforced_prohibited_words:
        return None

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {}) or {}
    current_working_directory = hook_input.get("cwd", "") or ""

    segments = collect_segments_to_inspect(
        tool_name, tool_input, current_working_directory
    )
    violation = find_prohibited_word_in_segments(enforced_prohibited_words, segments)
    if violation is None:
        return None

    word, label = violation
    block_message = (
        f"BLOCKED ({tool_name}): the word '{word}' must not appear in {label} "
        f"outside private repositories. Move it into private-configuration, or remove it."
    )
    return HandlerResult(
        decision="deny", reason=block_message, system_message=block_message
    )
