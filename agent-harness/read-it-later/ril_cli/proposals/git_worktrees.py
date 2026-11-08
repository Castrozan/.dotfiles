from __future__ import annotations

import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path

WORKTREES_DIRECTORY_NAME = ".worktrees"
GIT_TIMEOUT_SECONDS = 180


class GitOperationFailed(RuntimeError):
    pass


def git(directory: Path, *arguments: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(directory), *arguments],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise GitOperationFailed(f"git {' '.join(arguments)} timed out") from error
    if completed.returncode != 0:
        raise GitOperationFailed(
            f"git {' '.join(arguments)}: {completed.stderr.strip()}"
        )
    return completed.stdout.strip()


def remove_worktree(repository_directory: Path, worktree_path: Path) -> None:
    try:
        git(repository_directory, "worktree", "remove", "--force", str(worktree_path))
    except GitOperationFailed:
        shutil.rmtree(worktree_path, ignore_errors=True)
        git(repository_directory, "worktree", "prune")


@contextmanager
def branch_worktree(repository_directory: Path, branch: str, start_reference: str):
    worktree_path = repository_directory / WORKTREES_DIRECTORY_NAME / branch
    if worktree_path.exists():
        remove_worktree(repository_directory, worktree_path)
    git(
        repository_directory,
        "worktree",
        "add",
        "--quiet",
        "-B",
        branch,
        str(worktree_path),
        start_reference,
    )
    try:
        yield worktree_path
    finally:
        remove_worktree(repository_directory, worktree_path)


def fetch_reference(repository_directory: Path, branch: str) -> str:
    git(repository_directory, "fetch", "--quiet", "origin", branch)
    return f"origin/{branch}"


def commit_and_push(
    worktree_path: Path, relative_path: str, message: str, branch: str
) -> str:
    git(worktree_path, "add", "--", relative_path)
    git(worktree_path, "commit", "--quiet", "-m", message, "--", relative_path)
    git(worktree_path, "push", "--quiet", "origin", f"HEAD:refs/heads/{branch}")
    return git(worktree_path, "rev-parse", "HEAD")


def file_at_reference(
    repository_directory: Path, reference: str, relative_path: str
) -> str:
    return git(repository_directory, "show", f"{reference}:{relative_path}")
