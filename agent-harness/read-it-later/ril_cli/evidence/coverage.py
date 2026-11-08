from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from proposals.git_worktrees import git
from pull_requests import capture_slug

COMMIT_RECORD_SEPARATOR = "\x1e"
COMMIT_FIELD_SEPARATOR = "\x1f"
MAXIMUM_COMMITS_PER_CAPTURE = 10
MAXIMUM_PULL_REQUESTS_PER_CAPTURE = 10


@dataclass(frozen=True)
class Commit:
    short_hash: str
    subject: str
    message: str


def read_commit_log(
    repository_directory: Path, revision: str = "origin/main"
) -> list[Commit]:
    log_format = f"--format=%h{COMMIT_FIELD_SEPARATOR}%s{COMMIT_FIELD_SEPARATOR}%B{COMMIT_RECORD_SEPARATOR}"
    output = git(repository_directory, "log", revision, log_format)
    records = (record.strip("\n") for record in output.split(COMMIT_RECORD_SEPARATOR))
    return [
        Commit(*record.split(COMMIT_FIELD_SEPARATOR, 2)) for record in records if record
    ]


def commits_mentioning(commits: list[Commit], origin_id: str) -> list[str]:
    if not origin_id:
        return []
    mentioning = (
        f"{commit.short_hash} {commit.subject}"
        for commit in commits
        if origin_id in commit.message
    )
    return list(mentioning)[:MAXIMUM_COMMITS_PER_CAPTURE]


def mentions_any(haystacks: list[str], needles: list[str]) -> bool:
    return any(
        needle in haystack for haystack in haystacks for needle in needles if needle
    )


def pull_request_names_capture(
    pull_request: dict, capture_name: str, origin_id: str
) -> bool:
    branch = str(pull_request.get("headRefName", ""))
    body = str(pull_request.get("body") or "")
    named_by_capture = (
        capture_slug(capture_name) in branch or capture_name.removesuffix(".md") in body
    )
    return named_by_capture or mentions_any([branch, body], [origin_id])


def closed_pull_requests_naming(
    pull_requests: list[dict], capture_name: str, origin_id: str
) -> list[dict]:
    naming = [
        {
            "number": pull_request.get("number"),
            "title": pull_request.get("title", ""),
            "branch": pull_request.get("headRefName", ""),
            "state": pull_request.get("state", ""),
        }
        for pull_request in pull_requests
        if pull_request_names_capture(pull_request, capture_name, origin_id)
    ]
    return naming[:MAXIMUM_PULL_REQUESTS_PER_CAPTURE]
