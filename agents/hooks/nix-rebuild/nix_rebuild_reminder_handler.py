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
from nix_rebuild_ledger import read_and_clear_changed_nix_files  # noqa: E402
from nix_rebuild_obligation import outstanding_rebuild_obligation  # noqa: E402

REASON_BY_OBLIGATION = {
    "uncommitted": (
        "still uncommitted, so the rebuild has nothing to verify yet. Stage each "
        "file by path, commit, then run the rebuild"
    ),
    "unactivated": (
        "committed but not activated: no system activation has happened since they "
        "were edited. Run the rebuild"
    ),
}


def handle(hook_input: dict):
    if hook_input.get("stop_hook_active"):
        return None

    changed_nix_files = read_and_clear_changed_nix_files(
        hook_input.get("session_id", "")
    )
    if not changed_nix_files:
        return None

    obligation = outstanding_rebuild_obligation(changed_nix_files)
    if obligation is None:
        return None

    changed_file_names = ", ".join(
        sorted({os.path.basename(path) for path in changed_nix_files})
    )
    return HandlerResult(
        decision="block",
        reason=(
            f"Nix files changed this turn ({changed_file_names}) and are "
            f"{REASON_BY_OBLIGATION[obligation]}. A rebuild is how a nix change is "
            "tested, so an untested one is not finished."
        ),
    )
