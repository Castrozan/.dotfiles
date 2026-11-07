from __future__ import annotations

import os
import re
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

from shell_read_only_inspection_command import (  # noqa: E402
    offset_lies_in_text_the_shell_never_runs,
)

COMMANDS_THAT_BLOCK_UNTIL_CI_FINISHES = (
    r"(?<![-\w])gh\b[^|;&\n]*?(?<![-\w])run\s+watch\b",
    r"(?<![-\w])gh\b[^|;&\n]*?(?<![-\w])pr\s+checks\b[^|;&\n]*?--watch\b",
)

HELP_FLAGS_THAT_RETURN_IMMEDIATELY = r"--help\b|(?<!\w)-h\b"

ELEMENTS_OF_A_FOREGROUND_CI_POLLING_LOOP = (
    r"(?<![-\w])(?:for|while|until)(?![-\w])",
    r"(?<![-\w])gh\b[^|;&\n]*?(?<![-\w])(?:run|pr)\s+(?:list|view|status|checks)\b",
    r"(?<![-\w])sleep\s+\d",
)


def segment_containing_offset(command_string, offset):
    return re.split(r"[|;&\n]", command_string[offset:], maxsplit=1)[0]


def command_waits_on_ci_in_the_foreground(command_string):
    return any(
        _ci_wait_invocation_runs_in_the_foreground(command_string, match.start())
        for pattern in COMMANDS_THAT_BLOCK_UNTIL_CI_FINISHES
        for match in re.finditer(pattern, command_string)
    )


def _ci_wait_invocation_runs_in_the_foreground(command_string, offset):
    invocation_segment = segment_containing_offset(command_string, offset)
    if re.search(HELP_FLAGS_THAT_RETURN_IMMEDIATELY, invocation_segment):
        return False
    return not offset_lies_in_text_the_shell_never_runs(command_string, offset)


def command_polls_ci_in_a_foreground_loop(command_string):
    return all(
        any(
            not offset_lies_in_text_the_shell_never_runs(command_string, match.start())
            for match in re.finditer(element, command_string)
        )
        for element in ELEMENTS_OF_A_FOREGROUND_CI_POLLING_LOOP
    )
