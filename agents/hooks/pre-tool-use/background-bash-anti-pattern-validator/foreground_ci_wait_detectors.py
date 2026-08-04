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


def segment_containing_offset(command_string, offset):
    return re.split(r"[|;&\n]", command_string[offset:], maxsplit=1)[0]


def command_waits_on_ci_in_the_foreground(command_string):
    for pattern in COMMANDS_THAT_BLOCK_UNTIL_CI_FINISHES:
        for match in re.finditer(pattern, command_string):
            invocation_segment = segment_containing_offset(
                command_string, match.start()
            )
            if re.search(HELP_FLAGS_THAT_RETURN_IMMEDIATELY, invocation_segment):
                continue
            if offset_lies_in_text_the_shell_never_runs(command_string, match.start()):
                continue
            return True
    return False
