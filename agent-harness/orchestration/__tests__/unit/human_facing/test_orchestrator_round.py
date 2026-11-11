import json

import pytest
from hypothesis import given
from hypothesis import strategies as st
from orchestration_test_support import file_card, run_orchestrator, valid_card_document
from orchestrator_cli.round.rendering import LINK_CHARACTERS, with_short_links
from round_test_support import (
    ORCHESTRATOR,
    escalate,
    file_report,
    record_open_ask,
    report_document,
    run_round,
)

REQUESTS_HEADING = "### Your requests not yet verified done"
LONG_LINK = (
    "https://gitlab.example/group/platform/extensions/schedules/services/"
    "api-schedules/-/merge_requests/76"
)


@pytest.fixture
def directories(tmp_path):
    return tmp_path / "cards", tmp_path / "reports"


def test_the_round_shows_each_waiting_decision_with_every_option_and_every_session(
    monkeypatch, directories, capsys, notifications
):
    cards, reports = directories
    _, waiting = file_card(monkeypatch, cards, capsys)
    escalate(monkeypatch, cards, waiting)
    _, still_triaging = file_card(monkeypatch, cards, capsys)
    assert file_report(monkeypatch, reports, "Voyager", report_document()) == 0
    output = run_round(monkeypatch, cards, reports, capsys)
    card = valid_card_document()
    for expected in (
        waiting,
        card["question"],
        card["goal"],
        "keep",
        *(option["consequence"] for option in card["options"]),
        card["reasoning"],
        "Voyager",
        "blocked",
        "wait for the scope decision",
    ):
        assert " ".join(expected.split()) in output
    assert still_triaging not in output
    assert f"Reply with `{waiting}` and one option: drop, keep" in output
    assert "needs a decision:" not in output


def test_answered_cards_and_other_orchestrators_stay_out_of_the_round(
    monkeypatch, directories, capsys, notifications
):
    cards, reports = directories
    _, answered = file_card(monkeypatch, cards, capsys)
    escalate(monkeypatch, cards, answered)
    run_orchestrator(
        monkeypatch,
        cards,
        "answer",
        answered,
        "--choice",
        "drop",
        "--rationale",
        "cosmetic",
        "--by",
        "human",
        "--sender",
        "Medea",
    )
    other = run_orchestrator(
        monkeypatch,
        reports,
        "file",
        "--to",
        "someone-else",
        "--sender",
        "Astolfo",
        stdin_text=json.dumps(report_document()),
        command="report",
    )
    assert other == 0
    output = run_round(monkeypatch, cards, reports, capsys)
    assert answered not in output and "Astolfo" not in output
    assert "No decision is waiting for you." in output


def headings(output):
    return [line for line in output.splitlines() if line.startswith("### ")]


def test_the_round_runs_sessions_then_requests_then_decisions_and_ends_on_the_reply(
    monkeypatch, directories, tmp_path, capsys, notifications
):
    cards, reports = directories
    _, waiting = file_card(monkeypatch, cards, capsys)
    escalate(monkeypatch, cards, waiting)
    assert file_report(monkeypatch, reports, "Voyager", report_document()) == 0
    record_open_ask(tmp_path / "state", "L-20261110-000001", "merge these two mrs")
    output = run_round(monkeypatch, cards, reports, capsys)
    assert headings(output) == [
        "### Sessions",
        REQUESTS_HEADING,
        "### Decisions waiting for you",
    ]
    assert output.rstrip().endswith(
        f"Reply with `{waiting}` and one option: drop, keep"
    )
    assert "Full view" not in output and "orchestrator report show" not in output


def test_a_round_with_nothing_to_show_says_so_under_sessions_then_decisions(
    monkeypatch, directories, capsys, notifications
):
    cards, reports = directories
    assert run_round(monkeypatch, cards, reports, capsys) == (
        "### Sessions\n\n"
        "No session has filed a report.\n\n"
        "### Decisions waiting for you\n\n"
        "No decision is waiting for you.\n"
    )


def test_the_requests_section_says_what_it_lists_and_what_makes_a_row_leave(
    monkeypatch, directories, tmp_path, capsys, notifications
):
    cards, reports = directories
    state_home = tmp_path / "state"
    record_open_ask(state_home, "L-20261110-000001", "merge these two mrs")
    record_open_ask(state_home, "L-20261110-000002", "ship it", owner="w3E:p1")
    output = run_round(monkeypatch, cards, reports, capsys)
    assert (
        f"{REQUESTS_HEADING}\n\n"
        f"Each row is something you asked {ORCHESTRATOR} for, in your words. "
        f"It leaves once {ORCHESTRATOR} has checked the real result, "
        "not only a session's report.\n\n"
        "| # | You asked | Handled by | Asked |\n"
        "|---|---|---|---|\n"
        f"| 1 | merge these two mrs | {ORCHESTRATOR} | 0m ago |\n"
        "| 2 | ship it | w3E:p1 | 0m ago |\n"
    ) in output


def test_a_request_that_opens_with_a_long_link_still_shows_its_words(
    monkeypatch, directories, tmp_path, capsys, notifications
):
    cards, reports = directories
    words = f"{LONG_LINK} fix the review points"
    record_open_ask(tmp_path / "state", "L-20261110-000001", words)
    output = run_round(monkeypatch, cards, reports, capsys)
    assert "| 1 | …/api-schedules/-/merge_requests/76 fix the review points |" in output


LINK_SEGMENTS = st.text("abcdefghij0123456789-_.", min_size=1, max_size=30)
LINKS = st.lists(LINK_SEGMENTS, min_size=1, max_size=8).map(
    lambda segments: "https://" + "/".join(segments)
)
PLAIN_WORDS = st.text("abcdefghij,.!?", min_size=1, max_size=12)


@given(st.lists(st.one_of(LINKS, PLAIN_WORDS), min_size=1, max_size=8))
def test_every_link_keeps_at_most_its_tail_while_other_words_stay_untouched(tokens):
    shown = with_short_links(" ".join(tokens)).split(" ")
    assert len(shown) == len(tokens)
    for original, displayed in zip(tokens, shown, strict=True):
        if not original.startswith("https://") or len(original) <= LINK_CHARACTERS:
            assert displayed == original
            continue
        assert displayed.startswith("…")
        assert original.endswith(displayed[1:])
        assert 1 < len(displayed) <= LINK_CHARACTERS + 1
