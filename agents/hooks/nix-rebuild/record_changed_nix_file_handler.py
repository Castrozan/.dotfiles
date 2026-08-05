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

from changed_file_paths import collect_changed_file_paths  # noqa: E402
from nix_rebuild_ledger import append_changed_nix_file  # noqa: E402
from nix_file_location import (  # noqa: E402
    has_nix_file_extension,
    is_inside_dotfiles_repository,
)


def handle(hook_input: dict):
    session_id = hook_input.get("session_id", "")
    for changed_path in collect_changed_file_paths(hook_input):
        if has_nix_file_extension(changed_path) and is_inside_dotfiles_repository(
            changed_path
        ):
            append_changed_nix_file(session_id, os.path.abspath(changed_path))
    return None
