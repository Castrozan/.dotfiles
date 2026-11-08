from __future__ import annotations

import re

GROUP_BRANCH_PREFIX = "ril-group-"
DECISIONS_DIRECTORY = "agent-harness/read-it-later/decisions"
WATCHER_COMMENT_MARKER = "<!-- ril-watcher -->"
TOPIC_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
NON_SLUG_CHARACTERS = re.compile(r"[^a-z0-9]+")


def capture_slug(capture_name: str) -> str:
    without_suffix = capture_name.removesuffix(".md")
    return NON_SLUG_CHARACTERS.sub("-", without_suffix.lower()).strip("-")


def group_branch_name(proposal_date: str, topic_slug: str) -> str:
    return f"{GROUP_BRANCH_PREFIX}{proposal_date}-{topic_slug}"


def decision_path_for_branch(branch: str) -> str:
    return f"{DECISIONS_DIRECTORY}/{branch.removeprefix(GROUP_BRANCH_PREFIX)}.md"


def is_group_branch(branch: str) -> bool:
    return branch.startswith(GROUP_BRANCH_PREFIX)


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
        for fingerprint in map(unanswered_response_fingerprint, pull_requests)
        if fingerprint
    )


def signed_by_the_watcher(body: str) -> str:
    return f"{body.rstrip()}\n\n{WATCHER_COMMENT_MARKER}\n"
