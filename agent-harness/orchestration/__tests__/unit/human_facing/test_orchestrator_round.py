import json

import pytest
from orchestration_test_support import file_card, run_orchestrator, valid_card_document
from round_test_support import (
    escalate,
    file_report,
    report_document,
    run_round,
)


def readable_text(output):
    columns = {}
    for line in output.splitlines():
        if " │ " in line:
            for index, cell in enumerate(line.split(" │ ")):
                columns.setdefault(index, []).append(cell)
    column_text = [" ".join(" ".join(cells).split()) for cells in columns.values()]
    return " | ".join([" ".join(output.split()), *column_text])


@pytest.fixture
def directories(tmp_path):
    return tmp_path / "cards", tmp_path / "reports"


def test_the_round_shows_each_waiting_decision_with_every_option_then_every_session(
    monkeypatch, directories, capsys, notifications
):
    cards, reports = directories
    _, waiting = file_card(monkeypatch, cards, capsys)
    escalate(monkeypatch, cards, waiting)
    _, still_triaging = file_card(monkeypatch, cards, capsys)
    assert file_report(monkeypatch, reports, "Voyager", report_document()) == 0
    output = run_round(monkeypatch, cards, reports, capsys)
    card = valid_card_document()
    flattened = readable_text(output)
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
        assert " ".join(expected.split()) in flattened
    assert still_triaging not in output
    assert f"Reply with {waiting} and one option: drop, keep" in output
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
