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


def session_identifier_from_command(harness_name: str, command_line: str) -> str | None:
    words = command_words(command_line)
    if harness_name == "claude":
        session_flags = {"--resume", "--session-id", "-r"}
    elif harness_name == "opencode":
        session_flags = {"--session", "-s"}
    else:
        session_flags = set()
    for index, word in enumerate(words):
        if word in session_flags and index + 1 < len(words):
            candidate_session_identifier = words[index + 1]
            if not candidate_session_identifier.startswith("-"):
                return candidate_session_identifier
        for session_flag in session_flags:
            if word.startswith(f"{session_flag}="):
                candidate_session_identifier = word.removeprefix(f"{session_flag}=")
                if not candidate_session_identifier.startswith("-"):
                    return candidate_session_identifier
    if harness_name == "codex":
        return codex_session_identifier_from_command_words(words)
    return None


def codex_resume_arguments(words: list[str]) -> list[str] | None:
    word_index = 1
    while word_index < len(words):
        word = words[word_index]
        if word == "resume":
            return words[word_index + 1 :]
        if word == "--":
            return None
        if word in CODEX_OPTIONS_WITH_VALUES:
            word_index += 2
            continue
        if word.startswith("-"):
            word_index += 1
            continue
        return None
    return None


def codex_session_identifier_from_command_words(words: list[str]) -> str | None:
    resume_arguments = codex_resume_arguments(words)
    if resume_arguments is None or "--last" in resume_arguments:
        return None
    if any(
        word == "--image"
        or word.startswith("--image=")
        or word == "-i"
        or (word.startswith("-i") and len(word) > 2)
        for word in resume_arguments
    ):
        return None
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


def resume_command_for(harness_name: str, session_identifier: str | None) -> list[str]:
    if harness_name == "claude":
        if session_identifier is not None:
            return ["claude", "--resume", session_identifier]
        return ["claude", "--continue"]
    if harness_name == "codex":
        if session_identifier is not None:
            return ["codex", "resume", session_identifier]
        return ["codex", "resume", "--last"]
    if harness_name == "opencode":
        if session_identifier is not None:
            return ["opencode", "--session", session_identifier]
        return ["opencode", "--continue"]
    raise ValueError(f"unsupported harness: {harness_name}")


def harness_and_session_from_resume_command(
    resume_command: str | None,
) -> tuple[str | None, str | None]:
    if resume_command is None:
        return None, None
    harness_name = harness_name_for_command(resume_command)
    if harness_name is None:
        return None, None
    return harness_name, session_identifier_from_command(harness_name, resume_command)
