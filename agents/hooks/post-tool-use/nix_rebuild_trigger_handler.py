from __future__ import annotations

import os
import sys
from pathlib import Path

_MODULE_DIRECTORY = Path(__file__).resolve().parent
for _shared_module_candidate_directory in (
    _MODULE_DIRECTORY,
    _MODULE_DIRECTORY.parent / "common",
):
    _shared_module_candidate_path = str(_shared_module_candidate_directory)
    if (
        _shared_module_candidate_directory.is_dir()
        and _shared_module_candidate_path not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_path)

from changed_file_paths import collect_changed_file_paths  # noqa: E402
from hook_dispatch import HandlerResult  # noqa: E402

NIX_FILE_EXTENSIONS = [
    ".nix",
]


def has_nix_file_extension(path: str) -> bool:
    if not path:
        return False

    for extension in NIX_FILE_EXTENSIONS:
        if path.endswith(extension):
            return True

    return False


def handle(hook_input: dict):
    changed_nix_files = [
        path
        for path in collect_changed_file_paths(hook_input)
        if has_nix_file_extension(path)
    ]

    if not changed_nix_files:
        return None

    changed_nix_file_names = ", ".join(
        sorted({os.path.basename(path) for path in changed_nix_files})
    )
    mandatory_rebuild_message = (
        f"MANDATORY: {changed_nix_file_names} changed. "
        "You MUST stage, commit, and run the rebuild "
        "before responding to the user. "
        "Do not skip. Untested nix changes are not changes."
    )
    return HandlerResult(
        additional_context=mandatory_rebuild_message,
        system_message=mandatory_rebuild_message,
    )
