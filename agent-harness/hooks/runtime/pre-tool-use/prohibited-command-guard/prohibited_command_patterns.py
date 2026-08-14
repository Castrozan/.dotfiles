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

from ci_owned_command_patterns import CI_OWNED_BASH_COMMAND_PATTERNS  # noqa: E402
from local_operation_command_patterns import (  # noqa: E402
    LOCAL_OPERATION_BASH_COMMAND_PATTERNS,
)

PROHIBITED_BASH_COMMAND_PATTERNS = [
    *CI_OWNED_BASH_COMMAND_PATTERNS,
    *LOCAL_OPERATION_BASH_COMMAND_PATTERNS,
]

PROHIBITED_FILE_PATH_PATTERNS = [
    (
        r"(?:^|[\s/])castrozan/\.?dotfiles(?:/|$)",
        "Writing under castrozan/.dotfiles is prohibited; repo must not live on disk.",
    ),
]

PROHIBITED_PATTERNS_BY_TOOL = {
    "Bash": PROHIBITED_BASH_COMMAND_PATTERNS,
    "Write": PROHIBITED_FILE_PATH_PATTERNS,
    "Edit": PROHIBITED_FILE_PATH_PATTERNS,
    "NotebookEdit": PROHIBITED_FILE_PATH_PATTERNS,
    "apply_patch": PROHIBITED_FILE_PATH_PATTERNS,
}
