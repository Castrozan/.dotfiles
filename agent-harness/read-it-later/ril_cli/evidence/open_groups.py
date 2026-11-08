from __future__ import annotations

from pathlib import Path

from proposals.decision_files import DecisionFileUnreadable, parse_decision_file
from proposals.git_worktrees import GitOperationFailed, file_at_reference, git
from pull_requests import decision_path_for_branch


def fetch_branches(repository_directory: Path, branches: list[str]) -> None:
    if branches:
        git(repository_directory, "fetch", "--quiet", "origin", *branches)


def open_group(repository_directory: Path, pull_request: dict) -> dict:
    branch = str(pull_request["headRefName"])
    summary = {
        "number": pull_request["number"],
        "title": pull_request.get("title", ""),
        "branch": branch,
        "decision_file": decision_path_for_branch(branch),
    }
    try:
        group = parse_decision_file(
            file_at_reference(
                repository_directory,
                f"origin/{branch}",
                decision_path_for_branch(branch),
            )
        )
    except (GitOperationFailed, DecisionFileUnreadable) as error:
        return {**summary, "bundle_goal": "", "captures": [], "unreadable": str(error)}
    return {
        **summary,
        "topic_slug": group["topic_slug"],
        "bundle_goal": group["bundle_goal"],
        "captures": [card["capture"] for card in group["cards"]],
    }


def open_groups(repository_directory: Path, pull_requests: list[dict]) -> list[dict]:
    fetch_branches(
        repository_directory,
        [str(pull_request["headRefName"]) for pull_request in pull_requests],
    )
    return [
        open_group(repository_directory, pull_request) for pull_request in pull_requests
    ]


def captures_listed_in(groups: list[dict]) -> set[str]:
    return {capture for group in groups for capture in group["captures"]}
