from __future__ import annotations

import re
import subprocess
from pathlib import Path

from forge.native import open_change_requests
from forge.repository import resolve_repository

RIL_BRANCH_PREFIX = "ril-"
WATCHER_COMMENT_MARKER = "<!-- ril-watcher -->"
NON_SLUG_CHARACTERS = re.compile(r"[^a-z0-9]+")


class PullRequestLookupUnavailable(RuntimeError):
    pass


def capture_slug(capture_name: str) -> str:
    without_suffix = capture_name[:-3] if capture_name.endswith(".md") else capture_name
    return NON_SLUG_CHARACTERS.sub("-", without_suffix.lower()).strip("-")


def capture_branch_name(capture_name: str) -> str:
    return f"{RIL_BRANCH_PREFIX}{capture_slug(capture_name)}"


def capture_decision_path(capture_name: str) -> str:
    return f"agent-harness/read-it-later/decisions/{capture_slug(capture_name)}.md"


def open_ril_pull_requests(repository_directory: Path) -> list[dict]:
    try:
        repository = resolve_repository(repository_directory)
        listed_pull_requests = open_change_requests(repository, RIL_BRANCH_PREFIX)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        raise PullRequestLookupUnavailable(str(error)) from error
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
