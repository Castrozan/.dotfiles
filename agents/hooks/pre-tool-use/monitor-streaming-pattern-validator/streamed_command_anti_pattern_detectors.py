#!/usr/bin/env python3

import re
import sys
from pathlib import Path

hook_script_directory = Path(__file__).resolve().parent
sys.path.insert(0, str(hook_script_directory))
shared_common_hook_modules_directory = hook_script_directory.parent / "common"
if shared_common_hook_modules_directory.is_dir():
    sys.path.insert(0, str(shared_common_hook_modules_directory))

from interactive_command_hang_detectors import (  # noqa: E402
    command_launches_interactive_full_screen_program,
    command_runs_git_subcommand_that_opens_an_editor,
)

STDERR_HEAVY_COMMAND_PATTERNS = (
    r"\bgit\s+(fetch|push|pull|clone|clean|gc)\b",
    r"\bcurl\s+[^|]*-v",
    r"\bnpm\s+(install|ci|run|update)\b",
    r"\byarn\s+(install|add)\b",
    r"\bpnpm\s+(install|add)\b",
    r"\bcargo\s+(build|test|run|check)\b",
    r"\bmake\b",
    r"\bkubectl\s+\w+\s+.*-v\b",
)


def command_invokes_python_with_buffered_stdout(command_string):
    invokes_python = bool(re.search(r"\bpython3?\b", command_string))
    if not invokes_python:
        return False
    python_call_has_unbuffered_flag = bool(
        re.search(
            r"\bpython3?\b[^|;&\n]*?(?<!\S)-[A-Za-z]*u[A-Za-z]*\b", command_string
        )
    )
    environment_disables_python_buffering = "PYTHONUNBUFFERED=" in command_string
    return not (
        python_call_has_unbuffered_flag or environment_disables_python_buffering
    )


def command_pipes_into_grep_without_line_buffered_flag(command_string):
    pipe_into_grep_pattern = re.compile(
        r"\|\s*(?:[A-Z_]+=\S+\s+)*(?:grep|egrep|fgrep)\b([^|]*)"
    )
    for matched_grep_invocation in pipe_into_grep_pattern.finditer(command_string):
        invocation_flags = matched_grep_invocation.group(1)
        if "--line-buffered" not in invocation_flags:
            return True
    return False


def command_pipes_into_sed_without_unbuffered_flag(command_string):
    pipe_into_sed_pattern = re.compile(r"\|\s*(?:[A-Z_]+=\S+\s+)*sed\b([^|]*)")
    for matched_sed_invocation in pipe_into_sed_pattern.finditer(command_string):
        invocation_flags = matched_sed_invocation.group(1)
        sed_has_unbuffered_flag = bool(
            re.search(r"(?<![A-Za-z0-9])-u\b|--unbuffered\b", invocation_flags)
        )
        if not sed_has_unbuffered_flag:
            return True
    return False


def command_pipes_into_awk(command_string):
    return bool(re.search(r"\|\s*(?:awk|gawk|nawk|mawk)\b", command_string))


def command_runs_known_stderr_heavy_program_without_redirect(command_string):
    if re.search(r"2>&1\b", command_string):
        return False
    return any(
        re.search(pattern, command_string) for pattern in STDERR_HEAVY_COMMAND_PATTERNS
    )


def command_waits_blindly_on_a_timed_sleep(command_string):
    has_timed_sleep = bool(
        re.search(r"(?<![A-Za-z0-9_/.-])sleep\s+[0-9.]", command_string)
    )
    if not has_timed_sleep:
        return False
    sleep_paces_a_condition_loop = bool(
        re.search(r"(?<![A-Za-z0-9_])(?:until|while)(?![A-Za-z0-9_])", command_string)
    )
    return not sleep_paces_a_condition_loop


PATTERN_DETECTORS_BY_RULE_NAME = {
    "python-without-u": command_invokes_python_with_buffered_stdout,
    "grep-without-line-buffered": command_pipes_into_grep_without_line_buffered_flag,
    "sed-without-u": command_pipes_into_sed_without_unbuffered_flag,
    "awk-needs-fflush": command_pipes_into_awk,
    "stderr-only-without-redirect": command_runs_known_stderr_heavy_program_without_redirect,
}

HANG_PATTERN_DETECTORS_BY_RULE_NAME = {
    "interactive-editor-or-full-screen-tui": command_launches_interactive_full_screen_program,
    "command-that-opens-an-editor": command_runs_git_subcommand_that_opens_an_editor,
}

BUSY_WAIT_PATTERN_DETECTORS_BY_RULE_NAME = {
    "blind-sleep-wait": command_waits_blindly_on_a_timed_sleep,
}


def find_streaming_anti_patterns_in_command(command_string):
    return [
        rule_name
        for rule_name, detector in PATTERN_DETECTORS_BY_RULE_NAME.items()
        if detector(command_string)
    ]


def find_hang_anti_patterns_in_command(command_string):
    return [
        rule_name
        for rule_name, detector in HANG_PATTERN_DETECTORS_BY_RULE_NAME.items()
        if detector(command_string)
    ]


def find_busy_wait_anti_patterns_in_command(command_string):
    return [
        rule_name
        for rule_name, detector in BUSY_WAIT_PATTERN_DETECTORS_BY_RULE_NAME.items()
        if detector(command_string)
    ]
