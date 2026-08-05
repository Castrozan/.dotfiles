import re

COMMAND_SEGMENT_START = r"(?:^|[\n;&|(`]|&&|\|\|)\s*"
OPTIONAL_ENVIRONMENT_ASSIGNMENT_PREFIX = r"(?:[A-Za-z_][A-Za-z0-9_]*=\S+\s+)*"
OPTIONAL_PRIVILEGE_ELEVATION_PREFIX = r"(?:sudo\s+|doas\s+|env\s+)*"

INTERACTIVE_FULL_SCREEN_PROGRAMS_LONGEST_FIRST = (
    "emacsclient",
    "emacs",
    "vimdiff",
    "nvim",
    "vim",
    "nano",
    "micro",
    "pico",
    "joe",
    "htop",
    "btop",
    "top",
    "vi",
)

NON_INTERACTIVE_ESCAPE_FLAGS_BY_PROGRAM = {
    "vim": (r"--headless\b", r"(?<!\w)-es\b", r"(?<!\w)-Es\b"),
    "nvim": (r"--headless\b", r"(?<!\w)-es\b", r"(?<!\w)-Es\b"),
    "emacs": (r"--batch\b", r"(?<!\w)-batch\b"),
    "emacsclient": (r"--eval\b", r"(?<!\w)-e\b"),
    "top": (r"(?<!\w)-b\b", r"(?<!\w)-l\b"),
}

GIT_COMMIT_MESSAGE_SOURCE_FLAGS = (
    r"(?<!\w)-[A-Za-z]*m\b",
    r"--message\b",
    r"--message=",
    r"(?<!\w)-[A-Za-z]*F\b",
    r"--file\b",
    r"--file=",
    r"(?<!\w)-C\b",
    r"--reuse-message\b",
    r"--reedit-message\b",
    r"--no-edit\b",
)

GIT_TAG_MESSAGE_SOURCE_FLAGS = (
    r"(?<!\w)-[A-Za-z]*m\b",
    r"--message\b",
    r"--message=",
    r"(?<!\w)-[A-Za-z]*F\b",
    r"--file\b",
    r"--file=",
)


def segment_following_match_until_next_separator(command_string, match):
    return re.split(r"[|;&\n]", command_string[match.start() :], maxsplit=1)[0]


def command_launches_interactive_full_screen_program(command_string):
    program_alternation = "|".join(INTERACTIVE_FULL_SCREEN_PROGRAMS_LONGEST_FIRST)
    interactive_program_invocation_pattern = re.compile(
        COMMAND_SEGMENT_START
        + OPTIONAL_ENVIRONMENT_ASSIGNMENT_PREFIX
        + OPTIONAL_PRIVILEGE_ELEVATION_PREFIX
        + rf"(?P<program>{program_alternation})\b"
    )
    for match in interactive_program_invocation_pattern.finditer(command_string):
        invoked_program = match.group("program")
        invocation_segment = segment_following_match_until_next_separator(
            command_string, match
        )
        escape_flags = NON_INTERACTIVE_ESCAPE_FLAGS_BY_PROGRAM.get(invoked_program, ())
        if any(re.search(flag, invocation_segment) for flag in escape_flags):
            continue
        return True
    return False


def command_runs_git_subcommand_that_opens_an_editor(command_string):
    commit_match = re.search(
        r"(?<![-\w])git\b[^|;&\n]*?(?<![-\w])commit\b([^|;&\n]*)", command_string
    )
    if commit_match:
        commit_arguments = commit_match.group(1)
        commit_has_message_source = any(
            re.search(flag, commit_arguments)
            for flag in GIT_COMMIT_MESSAGE_SOURCE_FLAGS
        )
        if not commit_has_message_source:
            return True

    rebase_opens_todo_editor = bool(
        re.search(
            r"(?<![-\w])git\b[^|;&\n]*?(?<![-\w])rebase\b[^|;&\n]*?(?:-i\b|--interactive\b)",
            command_string,
        )
    )
    if rebase_opens_todo_editor:
        return True

    tag_match = re.search(
        r"(?<![-\w])git\b[^|;&\n]*?(?<![-\w])tag\b([^|;&\n]*)", command_string
    )
    if tag_match:
        tag_arguments = tag_match.group(1)
        tag_opens_editor = bool(
            re.search(r"(?<!\w)-[A-Za-z]*[as]\b|--annotate\b|--sign\b", tag_arguments)
        )
        tag_has_message_source = any(
            re.search(flag, tag_arguments) for flag in GIT_TAG_MESSAGE_SOURCE_FLAGS
        )
        if tag_opens_editor and not tag_has_message_source:
            return True

    return False


HAMMERSPOON_IPC_INVOCATION = (
    COMMAND_SEGMENT_START
    + OPTIONAL_ENVIRONMENT_ASSIGNMENT_PREFIX
    + r"(?P<timeout_wrapper>g?timeout\s+\S+\s+)?"
    + r"(?:\S*/)?hs\b"
)


def command_invokes_hammerspoon_ipc_without_timeout(command_string):
    for match in re.finditer(HAMMERSPOON_IPC_INVOCATION, command_string):
        invocation_segment = segment_following_match_until_next_separator(
            command_string, match
        )
        if not re.search(r"(?<!\w)-c\b", invocation_segment):
            continue
        if match.group("timeout_wrapper"):
            continue
        return True
    return False
