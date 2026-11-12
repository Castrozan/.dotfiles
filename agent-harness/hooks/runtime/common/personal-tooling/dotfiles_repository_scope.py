from __future__ import annotations

import os
import re

PERSONAL_TOOLING_REPOSITORIES = frozenset(
    (
        ".dotfiles",
        "dotfiles-private",
        "private-config",
        "clawde",
        "agent-evals",
        "herdr",
        "herdr-pace",
        "wellput",
        "cache-tax",
        "cc-crayon",
        "airquote",
        "arr-stack",
    )
)
GITHUB_REMOTE = re.compile(
    r"(?:git@github\.com:|(?:https?|ssh|git)://(?:[^/@]+@)?github\.com(?::[0-9]+)?/)([^/]+)/([^/]+)/?",
    re.IGNORECASE,
)


def remote_identifies_personal_tooling(remote: str) -> bool:
    match = GITHUB_REMOTE.fullmatch(remote.strip())
    return bool(
        match
        and match[1].casefold() == "castrozan"
        and match[2].casefold().removesuffix(".git") in PERSONAL_TOOLING_REPOSITORIES
    )


def canonical_personal_tooling_path(directory: str) -> bool:
    resolved = os.path.realpath(directory)
    return any(
        resolved == root or resolved.startswith(root + os.sep)
        for root in (
            os.path.realpath(os.path.expanduser("~/.dotfiles")),
            os.path.realpath(os.path.expanduser("~/zanoni-system")),
        )
    )


def git_repository_is_personal_tooling(directory: str) -> bool:
    import subprocess

    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                directory,
                "config",
                "--local",
                "--get-regexp",
                r"^remote\..*\.url$",
            ],
            capture_output=True,
            text=True,
            timeout=0.5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if result.returncode != 0:
        return False
    for line in result.stdout.splitlines():
        fields = line.split(maxsplit=1)
        if len(fields) != 2:
            continue
        remote = fields[1]
        if remote_identifies_personal_tooling(remote):
            return True
        local_path = remote.removeprefix("file://")
        if os.path.isabs(local_path) and canonical_personal_tooling_path(local_path):
            return True
    return False


def linked_worktree_is_personal_tooling(directory: str) -> bool:
    git_file = os.path.join(directory, ".git")
    if not os.path.isfile(git_file):
        return False
    try:
        with open(git_file, encoding="utf-8") as stream:
            pointer = stream.read(4096).strip()
    except (OSError, UnicodeError):
        return False
    if not pointer.startswith("gitdir:"):
        return False
    git_directory = os.path.realpath(
        os.path.join(directory, pointer.partition(":")[2].strip())
    )
    return canonical_personal_tooling_path(git_directory)


def repository_is_personal_tooling(directory: str) -> bool:
    if not isinstance(directory, str) or not directory or not os.path.isabs(directory):
        return False
    current = os.path.realpath(directory)
    if canonical_personal_tooling_path(current):
        return True
    while True:
        if os.path.isfile(
            os.path.join(current, "agent-harness/quality/evaluations/config.yaml")
        ) and os.path.isfile(
            os.path.join(current, "repository/flake-assembly/outputs.nix")
        ):
            return True
        if os.path.exists(os.path.join(current, ".git")) and (
            linked_worktree_is_personal_tooling(current)
            or git_repository_is_personal_tooling(current)
        ):
            return True
        parent = os.path.dirname(current)
        if parent == current:
            return False
        current = parent
