"""Collect git repository status for the session start banner."""

from typing import Any, Dict

from session_context_command_runner import run_cmd


def get_git_status() -> Dict[str, Any]:
    code, _ = run_cmd(["git", "rev-parse", "--is-inside-work-tree"])
    if code != 0:
        return {"is_repo": False}

    status: dict[str, Any] = {"is_repo": True}

    code, branch = run_cmd(["git", "branch", "--show-current"])
    if code == 0:
        status["branch"] = branch

    code, porcelain = run_cmd(["git", "status", "--porcelain"])
    if code == 0:
        lines = [line for line in porcelain.split("\n") if line.strip()]
        status["uncommitted"] = len(lines)
        status["staged"] = sum(1 for line in lines if line[0] != " " and line[0] != "?")
        status["untracked"] = sum(1 for line in lines if line.startswith("??"))

    code, ahead_behind = run_cmd(
        ["git", "rev-list", "--left-right", "--count", "@{u}...HEAD"]
    )
    if code == 0:
        parts = ahead_behind.split()
        if len(parts) == 2:
            status["behind"] = int(parts[0])
            status["ahead"] = int(parts[1])

    code, last_commit = run_cmd(
        ["git", "log", "-1", "--format=%h %s", "--date=relative"]
    )
    if code == 0:
        status["last_commit"] = last_commit[:60]

    return status
