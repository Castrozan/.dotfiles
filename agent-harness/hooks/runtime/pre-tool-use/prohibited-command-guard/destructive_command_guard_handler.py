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

from destructive_command_restriction import (  # noqa: E402
    destructive_patterns_for_this_session,
)
from prohibited_command_guard_handler import (  # noqa: E402
    denial_for_first_violation,
)


def handle(hook_input):
    tool_name = hook_input.get("tool_name", "")
    return denial_for_first_violation(
        hook_input, destructive_patterns_for_this_session(tool_name)
    )
