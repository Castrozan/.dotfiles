import json

import pytest
from orchestration_test_support import file_card, run_orchestrator, valid_card_document
from orchestrator_cli.decisions import card_limits
from orchestrator_cli.reports.status_reports import REPORT_TEXT_LIMITS
from orchestrator_cli.round.rendering import ROUND_WIDTH

ORCHESTRATOR = "orchestrator-session"


def report_document(**overrides):
    return {
        "goal": "retire hey-bot into the avatar",
        "state": "blocked",
        "done_check": "hey-bot is gone from the repo and chise",
        "progress": "inventory filed as a card",
        "next_step": "wait for the scope decision",
        **overrides,
    }


def file_report(monkeypatch, reports, sender, document):
    return run_orchestrator(
        monkeypatch,
        reports,
        "file",
        "--to",
        ORCHESTRATOR,
        "--sender",
        sender,
        stdin_text=json.dumps(document),
        command="report",
    )


def escalate(monkeypatch, cards, identifier):
    escalation = ["escalate", identifier, "--reason", "no-directive"]
    run_orchestrator(monkeypatch, cards, *escalation, "--missing", "no scope rule")


def run_round(monkeypatch, cards, reports, capsys):
    capsys.readouterr()
    exit_code = run_orchestrator(
        monkeypatch,
        cards,
        "--for",
        ORCHESTRATOR,
        "--reports-dir",
        str(reports),
        command="round",
    )
    assert exit_code == 0
    return capsys.readouterr().out


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
        "drop (recommended)",
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


def test_the_round_stays_within_its_width_at_every_field_limit(
    monkeypatch, directories, capsys, notifications
):
    cards, reports = directories
    longest = {
        field: "word " * (limit // 5)
        for field, limit in card_limits.CARD_TEXT_LIMITS.items()
    }
    longest["recommendation"] = "first"
    options = [
        {"label": label, "consequence": "word " * 40}
        for label in ("first", "second", "third", "fourth")
    ]
    document = valid_card_document(**longest, options=options)
    _, identifier = file_card(monkeypatch, cards, capsys, document)
    escalate(monkeypatch, cards, identifier)
    for index in range(8):
        longest_report = {
            field: "word " * (limit // 5) for field, limit in REPORT_TEXT_LIMITS.items()
        }
        assert (
            file_report(
                monkeypatch,
                reports,
                f"Servant {index}",
                report_document(**longest_report),
            )
            == 0
        )
    output = run_round(monkeypatch, cards, reports, capsys)
    assert max(len(line) for line in output.splitlines()) <= ROUND_WIDTH
    assert output.count("Servant ") == 8


def test_a_report_field_past_its_limit_is_refused_by_name(
    monkeypatch, directories, notifications
):
    _, reports = directories
    too_long = "x" * (REPORT_TEXT_LIMITS["progress"] + 1)
    document = report_document(progress=too_long)
    assert file_report(monkeypatch, reports, "Voyager", document) == 1
    assert not reports.exists() or list(reports.iterdir()) == []
