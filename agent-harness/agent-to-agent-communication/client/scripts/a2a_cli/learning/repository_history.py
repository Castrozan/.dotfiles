from __future__ import annotations

import subprocess

GIT_TIMEOUT_SECONDS = 20


def git_output(repository: str, arguments: list[str]) -> list[str]:
    completed = subprocess.run(
        ["git", "-C", repository, *arguments],
        capture_output=True,
        text=True,
        check=False,
        timeout=GIT_TIMEOUT_SECONDS,
    )
    if completed.returncode != 0:
        return []
    return [line for line in completed.stdout.splitlines() if line.strip()]


def files_changed_by(repository: str, commits: list[str]) -> list[str]:
    changed = {
        path
        for commit in commits
        for path in git_output(repository, ["show", "--format=", "--name-only", commit])
    }
    return sorted(changed)


def commits_touching_since(repository: str, commits: list[str]) -> list[str]:
    files = files_changed_by(repository, commits)
    if not files:
        return []
    later = set()
    for commit in commits:
        later.update(
            git_output(
                repository, ["log", "--format=%H", f"{commit}..HEAD", "--", *files]
            )
        )
    return sorted(later - set(commits))
