import json
import re
from datetime import datetime, timedelta, timezone

import pytest
from orchestration_test_support import file_card, valid_card_document
from orchestrator_cli.decisions import card_limits
from orchestrator_cli.reports.status_reports import REPORT_TEXT_LIMITS
from round_test_support import (
    ORCHESTRATOR,
    escalate,
    file_report,
    report_document,
    run_round,
)

SOURCE_LINES = 52
UNESCAPED_PIPE = re.compile(r"(?<!\\)\|")


@pytest.fixture
def directories(tmp_path):
    return tmp_path / "cards", tmp_path / "reports"


def words_filling(limit):
    return "word " * (limit // 5)


def write_open_asks(state_home, count):
    ledger = state_home / "orchestrator-ledger"
    ledger.mkdir(parents=True)
    for index in range(count):
        ask = {
            "id": f"L-20261109-00000{index}",
            "kind": "ask",
            "words": words_filling(400),
            "owner": "Servant-with-a-long-name",
            "orchestrator": ORCHESTRATOR,
            "state": "open",
            "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        (ledger / f"{ask['id']}.json").write_text(json.dumps(ask))


def test_two_decisions_six_sessions_and_open_asks_at_every_limit_fit_one_screen(
    monkeypatch, directories, tmp_path, capsys, notifications
):
    cards, reports = directories
    longest = {
        field: words_filling(limit)
        for field, limit in card_limits.CARD_TEXT_LIMITS.items()
    }
    longest["recommendation"] = "first"
    options = [
        {
            "label": label + words_filling(card_limits.OPTION_TEXT_LIMITS["label"] - 6),
            "consequence": words_filling(card_limits.OPTION_TEXT_LIMITS["consequence"]),
        }
        for label in ("first", "second", "third")
    ]
    options[0]["label"] = "first"
    for _ in range(2):
        document = valid_card_document(**longest, options=options)
        _, identifier = file_card(monkeypatch, cards, capsys, document)
        escalate(monkeypatch, cards, identifier)
    for index in range(6):
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
    write_open_asks(tmp_path / "state", 7)
    output = run_round(monkeypatch, cards, reports, capsys)
    assert len(output.splitlines()) <= SOURCE_LINES
    assert output.count("Servant-") == 6 + 5
    assert "2 more: `orchestrator ledger list`" in output


def write_report(reports, name, minutes_ago, **fields):
    template = json.loads(next(reports.glob("Voyager*.json")).read_text())
    updated = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    record = {
        **template,
        "name": name,
        "requester": name,
        "updated_at": updated.isoformat(timespec="seconds"),
        **fields,
    }
    (reports / f"{name}.json").write_text(json.dumps(record))


def test_finished_and_handed_over_sessions_leave_while_legacy_text_is_clipped(
    monkeypatch, directories, capsys, notifications
):
    cards, reports = directories
    assert file_report(monkeypatch, reports, "Voyager", report_document()) == 0
    write_report(reports, "Finished-long-ago", 120, state="done")
    write_report(reports, "Finished-just-now", 5, state="done")
    write_report(reports, "Handed-over", 1, state="handed-over")
    write_report(reports, "Oversized", 1, next_step="legacy " * 200)
    output = run_round(monkeypatch, cards, reports, capsys)
    assert "Finished-long-ago" not in output and "Handed-over" not in output
    assert "Finished-just-now" in output and "Voyager" in output
    assert "…" in output
    assert output.count("legacy") < 30


def test_a_pipe_in_a_cell_keeps_the_session_table_columns(
    monkeypatch, directories, capsys, notifications
):
    cards, reports = directories
    document = report_document(next_step="split a | b, c || d")
    assert file_report(monkeypatch, reports, "Voyager", document) == 0
    output = run_round(monkeypatch, cards, reports, capsys)
    rows = [line for line in output.splitlines() if line.startswith("| ")]
    assert len({len(UNESCAPED_PIPE.findall(row)) for row in rows}) == 1
    assert "a \\| b" in output


def test_a_report_field_past_its_limit_is_refused_by_name(
    monkeypatch, directories, notifications
):
    _, reports = directories
    too_long = "x" * (REPORT_TEXT_LIMITS["progress"] + 1)
    document = report_document(progress=too_long)
    assert file_report(monkeypatch, reports, "Voyager", document) == 1
    assert not reports.exists() or list(reports.iterdir()) == []
