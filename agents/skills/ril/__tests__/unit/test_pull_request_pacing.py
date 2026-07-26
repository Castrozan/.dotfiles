import subprocess
from pathlib import Path

import pytest
from commands import captures_without_an_open_pull_request
from pull_requests import (
    PullRequestLookupUnavailable,
    branches_with_open_pull_request,
    capture_branch_name,
    capture_decision_path,
    comments_awaiting_an_answer,
    open_ril_pull_requests,
    response_fingerprints,
    unanswered_response_fingerprint,
)

CAPTURE_NAME = "Tweet from A. L. Crego (2026-07-25 11-53-34).md"
WATCHER_REPLY = {"id": "c2", "body": "answered that\n\n<!-- ril-watcher -->"}
LUCAS_COMMENT = {"id": "c1", "body": "why not use the existing module?"}


def completed_process(stdout: str = "", stderr: str = "", returncode: int = 0):
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout=stdout, stderr=stderr
    )


def test_the_branch_and_decision_path_come_from_one_slug():
    assert capture_branch_name(CAPTURE_NAME) == (
        "ril-tweet-from-a-l-crego-2026-07-25-11-53-34"
    )
    assert capture_decision_path(CAPTURE_NAME) == (
        "ril/decisions/tweet-from-a-l-crego-2026-07-25-11-53-34.md"
    )


def test_the_slug_survives_punctuation_and_non_ascii():
    assert capture_branch_name("Tweet from (つ🪩益🪩)つ (2026-07-25 10-16-14).md") == (
        "ril-tweet-from-2026-07-25-10-16-14"
    )


def test_only_ril_branches_count_as_the_watchers_pull_requests(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_, **__: completed_process(
            stdout='[{"number":1,"headRefName":"ril-a","comments":[]},'
            '{"number":2,"headRefName":"feature-b","comments":[]}]'
        ),
    )

    listed = open_ril_pull_requests(Path("/repo"))

    assert [pull_request["number"] for pull_request in listed] == [1]


def test_a_failed_lookup_raises_rather_than_reporting_no_pull_requests(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_, **__: completed_process(
            stderr="gh: not authenticated", returncode=1
        ),
    )

    with pytest.raises(PullRequestLookupUnavailable):
        open_ril_pull_requests(Path("/repo"))


def test_a_comment_the_watcher_already_replied_to_is_no_longer_awaiting_an_answer():
    answered = {"number": 7, "comments": [LUCAS_COMMENT, WATCHER_REPLY]}

    assert comments_awaiting_an_answer(answered) == []
    assert unanswered_response_fingerprint(answered) == ""


def test_a_comment_arriving_after_the_watchers_reply_reopens_the_thread():
    reopened = {
        "number": 7,
        "comments": [LUCAS_COMMENT, WATCHER_REPLY, {"id": "c3", "body": "still no"}],
    }

    assert unanswered_response_fingerprint(reopened) == "7:c3"


def test_the_watchers_own_words_never_count_as_a_response_on_their_own():
    talking_to_itself = {"number": 7, "comments": [WATCHER_REPLY]}

    assert unanswered_response_fingerprint(talking_to_itself) == ""


def test_a_pull_request_with_no_comments_raises_no_response():
    assert unanswered_response_fingerprint({"number": 9, "comments": []}) == ""
    assert response_fingerprints([{"number": 9, "comments": []}]) == []


def test_the_newest_unanswered_comment_is_the_fingerprint():
    pull_request = {
        "number": 7,
        "comments": [{"id": "c1", "body": "wait"}, {"id": "c3", "body": "ship it"}],
    }

    assert unanswered_response_fingerprint(pull_request) == "7:c3"


def test_a_capture_already_carrying_a_pull_request_is_not_offered_again():
    pending = [
        {"name": CAPTURE_NAME, "state": "unworked", "captured": "2026-07-25 11:53:34"},
        {"name": "Older.md", "state": "unworked", "captured": "2026-07-24 09:00:00"},
    ]
    open_branches = branches_with_open_pull_request(
        [{"number": 1, "headRefName": capture_branch_name(CAPTURE_NAME)}]
    )

    remaining = captures_without_an_open_pull_request(pending, open_branches)

    assert [capture["name"] for capture in remaining] == ["Older.md"]


def test_a_capture_held_by_a_live_claim_is_not_offered_either():
    pending = [
        {"name": "Held.md", "state": "working", "captured": "2026-07-25 11:00:00"}
    ]

    assert captures_without_an_open_pull_request(pending, set()) == []
