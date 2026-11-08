from __future__ import annotations

import fcntl
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from application.card_actions import (
    CardActionContext,
    apply_session_bundle,
    apply_single_card,
)
from forge_adapter import ForgeAdapter, ForgeUnavailable
from proposals.decision_files import parse_decision_file
from proposals.git_worktrees import fetch_reference, file_at_reference
from pull_requests import (
    decision_path_for_branch,
    is_group_branch,
    written_by_the_watcher,
)

SETTLED_STATUSES = ("recorded", "already-done", "missing")
APPLICABLE_STATES = ("OPEN", "OPENED", "MERGED")
APPLY_LOCK_PATH = Path(tempfile.gettempdir()) / "ril-apply.lock"


class ApplyRefused(RuntimeError):
    pass


@dataclass(frozen=True)
class ApplyRequest:
    pull_request_number: int
    approval_comment_id: str
    repository_directory: Path
    forge: ForgeAdapter
    actions: CardActionContext


@contextmanager
def serial_apply_lock():
    with APPLY_LOCK_PATH.open("w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        yield


def approval_comment(pull_request: dict, comment_id: str) -> dict:
    matching = [
        comment
        for comment in pull_request.get("comments") or []
        if str(comment.get("id")) == comment_id
    ]
    if not matching:
        raise ApplyRefused(
            f"pull request {pull_request['number']} has no comment {comment_id}"
        )
    if written_by_the_watcher(matching[0]):
        raise ApplyRefused(
            f"comment {comment_id} is the watcher's own, not an approval"
        )
    return matching[0]


def instant(timestamp: str) -> datetime:
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


def split_by_approval(
    cards: list[dict], approved_at: str
) -> tuple[list[dict], list[dict]]:
    covered = [
        card for card in cards if instant(card["added_at"]) <= instant(approved_at)
    ]
    return covered, [card for card in cards if card not in covered]


def approved_group(request: ApplyRequest, pull_request: dict) -> dict:
    branch = str(pull_request.get("headRefName", ""))
    if str(pull_request.get("state", "")).upper() not in APPLICABLE_STATES:
        raise ApplyRefused(
            f"pull request {request.pull_request_number} is {pull_request.get('state')}"
        )
    if not is_group_branch(branch):
        raise ApplyRefused(
            f"pull request {request.pull_request_number} is not a RIL group"
        )
    reference = fetch_reference(request.repository_directory, branch)
    return parse_decision_file(
        file_at_reference(
            request.repository_directory, reference, decision_path_for_branch(branch)
        )
    )


def card_results(
    request: ApplyRequest, group: dict, covered: list[dict], pull_request: dict
) -> list[dict]:
    single_results = [
        apply_single_card(request.actions, card)
        for card in covered
        if card["action"] != "session"
    ]
    session_cards = [card for card in covered if card["action"] == "session"]
    if not session_cards:
        return single_results
    return single_results + apply_session_bundle(
        request.actions, group, session_cards, pull_request
    )


def merge_when_settled(
    request: ApplyRequest,
    pull_request: dict,
    results: list[dict],
    uncovered: list[dict],
) -> str:
    if str(pull_request.get("state", "")).upper() == "MERGED":
        return "already-merged"
    if uncovered or any(result["status"] not in SETTLED_STATUSES for result in results):
        return "not-merged"
    try:
        request.forge.merge(request.pull_request_number)
    except ForgeUnavailable as error:
        return f"merge-failed: {error}"
    return "merged"


def apply_pull_request(request: ApplyRequest) -> dict:
    with serial_apply_lock():
        pull_request = request.forge.pull_request(request.pull_request_number)
        approval = approval_comment(pull_request, request.approval_comment_id)
        group = approved_group(request, pull_request)
        covered, uncovered = split_by_approval(group["cards"], approval["createdAt"])
        results = card_results(request, group, covered, pull_request)
        return {
            "pull_request": request.pull_request_number,
            "results": results,
            "not_covered_by_the_approval": [card["capture"] for card in uncovered],
            "merge": merge_when_settled(request, pull_request, results, uncovered),
        }
