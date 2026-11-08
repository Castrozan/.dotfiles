from __future__ import annotations

import os
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path

from .directives import Directive

GIT_TIMEOUT_SECONDS = 60
PIN_PUSH_ATTEMPTS = 3
GITLINK_MODE = "160000"


class UserModelPublicationFailure(Exception):
    pass


def git(repository: Path, *arguments: str, index: Path | None = None) -> str:
    environment = {**os.environ, "GIT_INDEX_FILE": str(index)} if index else None
    try:
        completed = subprocess.run(
            ["git", "-C", str(repository), *arguments],
            capture_output=True,
            text=True,
            check=True,
            timeout=GIT_TIMEOUT_SECONDS,
            env=environment,
        )
    except subprocess.CalledProcessError as failure:
        raise UserModelPublicationFailure(
            f"git {arguments[0]} failed: {failure.stderr.strip()}"
        ) from failure
    except (OSError, subprocess.TimeoutExpired) as failure:
        raise UserModelPublicationFailure(
            f"git {arguments[0]} failed: {failure}"
        ) from failure
    return completed.stdout.strip()


def refresh_checkout(repository: Path) -> None:
    git(repository, "fetch", "-q", "origin")
    git(repository, "checkout", "-q", "--detach", "origin/main")


def commit_and_push(repository: Path, user_model: Path, message: str) -> None:
    git(repository, "add", "--", str(user_model))
    git(repository, "commit", "-q", "-m", message, "--", str(user_model))
    git(repository, "push", "-q", "origin", "HEAD:main")


def discard_unpublished(repository: Path, user_model: Path, previous_text: str) -> None:
    git(repository, "reset", "-q", "origin/main")
    user_model.write_text(previous_text, encoding="utf-8")


def superproject_of(repository: Path) -> Path | None:
    superproject = git(repository, "rev-parse", "--show-superproject-working-tree")
    return Path(superproject).resolve() if superproject else None


def pin_commit_on_origin(
    superproject: Path, pinned_path: str, revision: str, message: str
) -> str | None:
    git(superproject, "fetch", "-q", "origin")
    if git(superproject, "rev-parse", f"origin/main:{pinned_path}") == revision:
        return None
    with tempfile.TemporaryDirectory() as scratch:
        index = Path(scratch) / "index"
        git(superproject, "read-tree", "origin/main", index=index)
        gitlink = f"{GITLINK_MODE},{revision},{pinned_path}"
        git(superproject, "update-index", "--cacheinfo", gitlink, index=index)
        tree = git(superproject, "write-tree", index=index)
    return git(superproject, "commit-tree", tree, "-p", "origin/main", "-m", message)


def push_pin_fast_forward(
    superproject: Path, pinned_path: str, revision: str, message: str
) -> None:
    for attempt in range(1, PIN_PUSH_ATTEMPTS + 1):
        commit = pin_commit_on_origin(superproject, pinned_path, revision, message)
        if commit is None:
            return
        try:
            git(superproject, "push", "-q", "origin", f"{commit}:refs/heads/main")
            return
        except UserModelPublicationFailure:
            if attempt == PIN_PUSH_ATTEMPTS:
                raise


def publish_pin(repository: Path, identifier: str, message: str) -> None:
    superproject = superproject_of(repository)
    if superproject is None:
        return
    pinned_path = str(repository.relative_to(superproject))
    revision = git(repository, "rev-parse", "HEAD")
    try:
        push_pin_fast_forward(superproject, pinned_path, revision, message)
    except UserModelPublicationFailure as failure:
        raise UserModelPublicationFailure(
            f"{identifier} is pushed, but its pin did not reach the origin of "
            f"{superproject} because {failure}; do not add {identifier} again"
        ) from failure


def published_change(user_model: Path, change: Callable[[], Directive]) -> Directive:
    repository = Path(git(user_model.parent, "rev-parse", "--show-toplevel")).resolve()
    refresh_checkout(repository)
    previous_text = user_model.read_text(encoding="utf-8")
    directive = change()
    message = f"docs(user-model): record {directive.identifier}"
    try:
        commit_and_push(repository, user_model, message)
    except UserModelPublicationFailure:
        discard_unpublished(repository, user_model, previous_text)
        raise
    publish_pin(repository, directive.identifier, message)
    return directive
