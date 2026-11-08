from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path

from .directives import Directive

GIT_TIMEOUT_SECONDS = 60
PIN_COMMIT_PREFIX = "docs(user-model): record "


class UserModelPublicationFailure(Exception):
    pass


def git(repository: Path, *arguments: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repository), *arguments],
            capture_output=True,
            text=True,
            check=True,
            timeout=GIT_TIMEOUT_SECONDS,
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


def pin_in_superproject(repository: Path, message: str) -> Path | None:
    superproject = git(repository, "rev-parse", "--show-superproject-working-tree")
    if not superproject:
        return None
    pinned_path = str(repository.relative_to(Path(superproject).resolve()))
    git(Path(superproject), "add", "--", pinned_path)
    git(Path(superproject), "commit", "-q", "-m", message, "--", pinned_path)
    return Path(superproject)


def require_only_pins_unpushed(superproject: Path) -> None:
    git(superproject, "fetch", "-q", "origin")
    try:
        git(superproject, "merge-base", "--is-ancestor", "origin/main", "HEAD")
    except UserModelPublicationFailure as failure:
        raise UserModelPublicationFailure(
            "this checkout has diverged from origin/main"
        ) from failure
    unpushed = git(superproject, "log", "--format=%s", "origin/main..HEAD")
    others = [s for s in unpushed.splitlines() if not s.startswith(PIN_COMMIT_PREFIX)]
    if others:
        raise UserModelPublicationFailure(
            f"this checkout also holds {len(others)} unpushed commit(s) of other work"
        )


def push_pin(superproject: Path) -> None:
    require_only_pins_unpushed(superproject)
    git(superproject, "push", "-q", "origin", "HEAD:main")


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
    try:
        superproject = pin_in_superproject(repository, message)
    except UserModelPublicationFailure as failure:
        raise UserModelPublicationFailure(
            f"{directive.identifier} is pushed but not pinned, so do not add it "
            f"again: {failure}"
        ) from failure
    if superproject is not None:
        publish_pin(superproject, directive.identifier)
    return directive


def publish_pin(superproject: Path, identifier: str) -> None:
    try:
        push_pin(superproject)
    except UserModelPublicationFailure as failure:
        raise UserModelPublicationFailure(
            f"{identifier} is pushed and pinned in {superproject}, but the pin is not "
            f"pushed because {failure}; push it once that clears, and do not add "
            f"{identifier} again"
        ) from failure
