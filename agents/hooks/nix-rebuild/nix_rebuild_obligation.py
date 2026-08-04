from __future__ import annotations

import os
import subprocess

NIX_FILE_EXTENSIONS = (".nix",)

DOTFILES_REPOSITORY_MARKER_RELATIVE_PATH = (
    "agents/hooks/nix-rebuild/nix_rebuild_obligation.py"
)

SYSTEM_ACTIVATION_SYMLINK_PATH = "/run/current-system"

GIT_STATUS_TIMEOUT_SECONDS = 5


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


def paths_still_uncommitted(repository_path: str, file_paths: list[str]) -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "-C", repository_path, "status", "--porcelain", "--", *file_paths],
            capture_output=True,
            text=True,
            timeout=GIT_STATUS_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if completed.returncode != 0:
        return []
    return [line[3:].strip() for line in completed.stdout.splitlines() if line.strip()]


def last_system_activation_time() -> float | None:
    try:
        return os.lstat(SYSTEM_ACTIVATION_SYMLINK_PATH).st_mtime
    except OSError:
        return None


def newest_modification_time(file_paths: list[str]) -> float | None:
    modification_times = []
    for file_path in file_paths:
        try:
            modification_times.append(os.stat(file_path).st_mtime)
        except OSError:
            continue
    return max(modification_times) if modification_times else None


def outstanding_rebuild_obligation(changed_nix_files: list[str]):
    existing_files = [path for path in changed_nix_files if os.path.exists(path)]
    if not existing_files:
        return None

    repository_path = enclosing_dotfiles_repository(existing_files[0])
    if repository_path is None:
        return None

    uncommitted = paths_still_uncommitted(repository_path, existing_files)
    if uncommitted:
        return "uncommitted"

    activated_at = last_system_activation_time()
    edited_at = newest_modification_time(existing_files)
    if activated_at is None or edited_at is None:
        return None
    if activated_at < edited_at:
        return "unactivated"
    return None
