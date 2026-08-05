from __future__ import annotations

import os

NIX_FILE_EXTENSIONS = (".nix",)

DOTFILES_REPOSITORY_MARKER_RELATIVE_PATH = (
    "agent-harness/hooks/runtime/nix-rebuild/nix_file_location.py"
)


def has_nix_file_extension(path: str) -> bool:
    return bool(path) and path.endswith(NIX_FILE_EXTENSIONS)


def enclosing_dotfiles_repository(path: str):
    candidate = os.path.abspath(path)
    if os.path.isfile(candidate):
        candidate = os.path.dirname(candidate)
    while True:
        has_git_boundary = os.path.exists(os.path.join(candidate, ".git"))
        has_dotfiles_marker = os.path.exists(
            os.path.join(candidate, DOTFILES_REPOSITORY_MARKER_RELATIVE_PATH)
        )
        if has_git_boundary and has_dotfiles_marker:
            return candidate
        parent = os.path.dirname(candidate)
        if parent == candidate:
            return None
        candidate = parent


def is_inside_dotfiles_repository(path: str) -> bool:
    return enclosing_dotfiles_repository(path) is not None
