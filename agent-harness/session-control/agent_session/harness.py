import shlex
from pathlib import Path

from .processes import process_info_for

SUPPORTED_HARNESS_NAMES = frozenset({"claude", "codex", "opencode"})
CODEX_OPTIONS_WITH_VALUES = frozenset(
    {
        "-a",
        "--add-dir",
        "--ask-for-approval",
        "-c",
        "--cd",
        "--config",
        "--disable",
        "--enable",
        "-i",
        "--image",
        "--local-provider",
        "-m",
        "--model",
        "-p",
        "--profile",
        "--remote",
        "--remote-auth-token-env",
        "-s",
        "--sandbox",
        "-C",
    }
)
MAXIMUM_ANCESTOR_HOPS = 8


def command_words(command_line: str) -> list[str]:
    try:
        return shlex.split(command_line)
    except ValueError:
        return command_line.split()


def harness_name_for_command(command_line: str) -> str | None:
    words = command_words(command_line)
    if not words:
        return None
    executable_name = Path(words[0]).name
    if executable_name in SUPPORTED_HARNESS_NAMES:
        return executable_name
    return None


def find_agent_session(
    starting_process_identifier: int,
) -> tuple[int, str, str] | None:
    process_identifier = starting_process_identifier
    for _ in range(MAXIMUM_ANCESTOR_HOPS):
        process_information = process_info_for(process_identifier)
        if process_information is None:
            return None
        parent_process_identifier, command_line = process_information
        harness_name = harness_name_for_command(command_line)
        if harness_name is not None:
            return process_identifier, harness_name, command_line
        if parent_process_identifier in {0, 1, process_identifier}:
            return None
        process_identifier = parent_process_identifier
    return None


def _session_flags(harness_name):
    if harness_name == "claude":
        return {"--resume", "--session-id", "-r"}
    if harness_name == "opencode":
        return {"--session", "-s"}
    return set()


def _valid_session_identifier(candidate):
    if not candidate.startswith("-"):
        return candidate
    return None


def _separate_session_identifier(word, next_word, session_flags):
    if word in session_flags and next_word is not None:
        return _valid_session_identifier(next_word)
    return None


def _equals_session_identifier(word, session_flags):
    for session_flag in session_flags:
        if word.startswith(f"{session_flag}="):
            candidate_session_identifier = word.removeprefix(f"{session_flag}=")
            return _valid_session_identifier(candidate_session_identifier)
    return None


def _session_identifier_for_word(word, next_word, session_flags):
    candidate = _separate_session_identifier(word, next_word, session_flags)
    if candidate is not None:
        return candidate
    candidate = _equals_session_identifier(word, session_flags)
    if candidate is not None:
        return candidate
    return None


def session_identifier_from_command(harness_name: str, command_line: str) -> str | None:
    words = command_words(command_line)
    session_flags = _session_flags(harness_name)
    for index, word in enumerate(words):
        next_word = words[index + 1] if index + 1 < len(words) else None
        candidate = _session_identifier_for_word(word, next_word, session_flags)
        if candidate is not None:
            return candidate
    if harness_name == "codex":
        return codex_session_identifier_from_command_words(words)
    return None


def codex_resume_arguments(words: list[str]) -> list[str] | None:
    word_index = _codex_resume_word_index(words)
    if word_index is None:
        return None
    return words[word_index + 1 :]


def _scan_codex_resume_argument(words, word_index):
    word = words[word_index]
    if word == "resume":
        return True, word_index
    if word == "--":
        return None
    if word in CODEX_OPTIONS_WITH_VALUES:
        return False, word_index + 2
    if word.startswith("-"):
        return False, word_index + 1
    return None


def _codex_resume_word_index(words):
    word_index = 1
    while word_index < len(words):
        scan_result = _scan_codex_resume_argument(words, word_index)
        if scan_result is None:
            return None
        is_resume_command, next_index = scan_result
        if is_resume_command:
            return next_index
        word_index = next_index
    return None


def _is_codex_image_option(word):
    return (
        word == "--image"
        or word.startswith("--image=")
        or word == "-i"
        or (word.startswith("-i") and len(word) > 2)
    )


def _first_codex_positional_argument(resume_arguments):
    skip_next_word = False
    for word in resume_arguments:
        if skip_next_word:
            skip_next_word = False
            continue
        if word in CODEX_OPTIONS_WITH_VALUES:
            skip_next_word = True
            continue
        if word.startswith("-"):
            continue
        return word
    return None


def codex_session_identifier_from_command_words(words: list[str]) -> str | None:
    resume_arguments = codex_resume_arguments(words)
    if resume_arguments is None or "--last" in resume_arguments:
        return None
    if any(_is_codex_image_option(word) for word in resume_arguments):
        return None
    return _first_codex_positional_argument(resume_arguments)


def resume_command_for(harness_name: str, session_identifier: str) -> list[str]:
    if harness_name == "claude":
        return ["claude", "--resume", session_identifier]
    if harness_name == "codex":
        return ["codex", "resume", session_identifier]
    if harness_name == "opencode":
        return ["opencode", "--session", session_identifier]
    raise ValueError(f"unsupported harness: {harness_name}")
