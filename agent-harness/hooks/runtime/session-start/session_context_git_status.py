"""Collect git repository status for the session start banner."""

from __future__ import annotations

from typing import Any, Dict

from session_context_command_runner import run_cmd
from session_context_concurrent_gathering import gather_concurrently


def _porcelain_status_parts(porcelain):
    branch_headers = {}
    changed_entry_lines = []
    for line in porcelain.split("\n"):
        if line.startswith("# branch."):
            header_name, _, header_value = line[len("# ") :].partition(" ")
            branch_headers[header_name] = header_value
        elif line.strip():
            changed_entry_lines.append(line)
    return branch_headers, changed_entry_lines


def _add_branch_status(status, branch_headers):
    branch = branch_headers["branch.head"]
    if branch != "(detached)":
        status["branch"] = branch
    ahead_behind = branch_headers.get("branch.ab", "").split()
    if len(ahead_behind) == 2:
        status["ahead"] = int(ahead_behind[0].lstrip("+"))
        status["behind"] = int(ahead_behind[1].lstrip("-"))


def _changed_entry_counts(changed_entry_lines):
    return {
        "uncommitted": len(changed_entry_lines),
        "staged": sum(
            1
            for line in changed_entry_lines
            if line[:1] in ("1", "2") and line[2] != "."
        ),
        "untracked": sum(1 for line in changed_entry_lines if line.startswith("? ")),
    }


def parse_porcelain_v2_status(porcelain: str) -> Dict[str, Any]:
    branch_headers, changed_entry_lines = _porcelain_status_parts(porcelain)
    if "branch.head" not in branch_headers:
        return {}

    status: Dict[str, Any] = {"is_repo": True}
    _add_branch_status(status, branch_headers)
    status.update(_changed_entry_counts(changed_entry_lines))
    return status


def get_git_status() -> Dict[str, Any]:
    probes = gather_concurrently(
        {
            "status": lambda: run_cmd(["git", "status", "--porcelain=v2", "--branch"]),
            "last_commit": lambda: run_cmd(["git", "log", "-1", "--format=%h %s"]),
        }
    )

    status_code, porcelain = probes["status"]
    if status_code != 0:
        return {"is_repo": False}

    status = parse_porcelain_v2_status(porcelain)
    if not status:
        return {"is_repo": False}

    last_commit_code, last_commit = probes["last_commit"]
    if last_commit_code == 0 and last_commit:
        status["last_commit"] = last_commit[:60]

    return status
