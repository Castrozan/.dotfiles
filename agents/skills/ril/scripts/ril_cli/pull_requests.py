from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

RIL_BRANCH_PREFIX = "ril-"
WATCHER_COMMENT_MARKER = "<!-- ril-watcher -->"
PULL_REQUEST_QUERY_FIELDS = "number,headRefName,comments"
PULL_REQUEST_QUERY_LIMIT = "100"
NON_SLUG_CHARACTERS = re.compile(r"[^a-z0-9]+")


class PullRequestLookupUnavailable(RuntimeError):
    pass


def capture_slug(capture_name: str) -> str:
    without_suffix = capture_name[:-3] if capture_name.endswith(".md") else capture_name
    return NON_SLUG_CHARACTERS.sub("-", without_suffix.lower()).strip("-")


def capture_branch_name(capture_name: str) -> str:
    return f"{RIL_BRANCH_PREFIX}{capture_slug(capture_name)}"


def capture_decision_path(capture_name: str) -> str:
    return f"ril/decisions/{capture_slug(capture_name)}.md"


def open_ril_pull_requests(repository_directory: Path) -> list[dict]:
    completed_process = subprocess.run(
        [
            "gh",
            "pr",
            "list",
            "--state",
            "open",
            "--limit",
            PULL_REQUEST_QUERY_LIMIT,
            "--json",
            PULL_REQUEST_QUERY_FIELDS,
        ],
        cwd=repository_directory,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed_process.returncode != 0:
        raise PullRequestLookupUnavailable(completed_process.stderr.strip())
    try:
        listed_pull_requests = json.loads(completed_process.stdout or "[]")
    except json.JSONDecodeError as decode_error:
        raise PullRequestLookupUnavailable(str(decode_error)) from decode_error
    return [
        pull_request
        for pull_request in listed_pull_requests
        if str(pull_request.get("headRefName", "")).startswith(RIL_BRANCH_PREFIX)
    ]


def branches_with_open_pull_request(pull_requests: list[dict]) -> set[str]:
    return {str(pull_request.get("headRefName", "")) for pull_request in pull_requests}


def comment_identity(comment: dict) -> str:
    return str(comment.get("id") or comment.get("createdAt") or "")


def written_by_the_watcher(comment: dict) -> bool:
    return WATCHER_COMMENT_MARKER in str(comment.get("body", ""))


def comments_awaiting_an_answer(pull_request: dict) -> list[dict]:
    comment_thread = pull_request.get("comments") or []
    answered_through = max(
        (
            position
            for position, comment in enumerate(comment_thread)
            if written_by_the_watcher(comment)
        ),
        default=-1,
    )
    return [
        comment
        for comment in comment_thread[answered_through + 1 :]
        if not written_by_the_watcher(comment)
    ]


def unanswered_response_fingerprint(pull_request: dict) -> str:
    unanswered_comments = comments_awaiting_an_answer(pull_request)
    if not unanswered_comments:
        return ""
    return f"{pull_request.get('number')}:{comment_identity(unanswered_comments[-1])}"


def response_fingerprints(pull_requests: list[dict]) -> list[str]:
    return sorted(
        fingerprint
        for fingerprint in (
            unanswered_response_fingerprint(pull_request)
            for pull_request in pull_requests
        )
        if fingerprint
    )
