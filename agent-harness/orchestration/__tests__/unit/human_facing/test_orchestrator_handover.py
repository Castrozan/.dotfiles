import json
from datetime import datetime, timezone

import pytest
from orchestration_test_support import file_card, run_orchestrator
from orchestrator_cli.handover import cli as handover_cli
from orchestrator_cli.watch.herdr_events import HerdrUnavailable
from orchestrator_cli.watch.session_timeouts import (
    SessionRecords,
    WatchedSession,
    is_finished,
)

ORCHESTRATOR = "orchestrator-session"
REPORT = {
    "goal": "retire hey-bot into the avatar",
    "state": "working",
    "done_check": "hey-bot is gone",
    "progress": "inventory filed",
    "next_step": "port the wake word",
}


@pytest.fixture
def moved_panes(monkeypatch):
    moved = []

    def move(pane_id, label):
        moved.append((pane_id, label))
        return "wW:t9"

    monkeypatch.setattr(handover_cli, "move_pane_to_new_tab", move)
    return moved


def file_report(monkeypatch, reports):
    return run_orchestrator(
        monkeypatch,
        reports,
        "file",
        "--to",
        ORCHESTRATOR,
        "--sender",
        "Voyager",
        stdin_text=json.dumps(REPORT),
        command="report",
    )


def handover(monkeypatch, cards, reports):
    return run_orchestrator(
        monkeypatch,
        cards,
        "worker-pane",
        "--for",
        ORCHESTRATOR,
        "--reports-dir",
        str(reports),
        command="handover",
    )


def records(directory):
    return [json.loads(path.read_text()) for path in sorted(directory.glob("*.json"))]


def test_a_handover_closes_cards_retires_the_report_tells_the_peer_and_moves_it(
    monkeypatch, tmp_path, capsys, notifications, moved_panes
):
    cards, reports = tmp_path / "cards", tmp_path / "reports"
    _, identifier = file_card(monkeypatch, cards, capsys)
    assert file_report(monkeypatch, reports) == 0
    notifications.clear()
    assert handover(monkeypatch, cards, reports) == 0
    (card,) = records(cards)
    assert (
        card["state"] == "withdrawn" and "handed over" in card["withdrawal"]["reason"]
    )
    (report,) = records(reports)
    assert report["state"] == "handed-over"
    assert [target for target, _, _ in notifications] == ["worker-pane"]
    assert "drives this session directly" in notifications[0][2]
    assert moved_panes == [("worker-pane", "Voyager")]
    assert identifier in capsys.readouterr().out
    session = WatchedSession("worker-pane", "working", datetime.now(timezone.utc))
    assert is_finished(session, SessionRecords({}, {"worker-pane": "handed-over"}))


def test_a_handed_over_session_leaves_the_round(
    monkeypatch, tmp_path, capsys, notifications, moved_panes
):
    cards, reports = tmp_path / "cards", tmp_path / "reports"
    file_report(monkeypatch, reports)
    handover(monkeypatch, cards, reports)
    capsys.readouterr()
    round_arguments = ["--for", ORCHESTRATOR, "--reports-dir", str(reports)]
    run_orchestrator(monkeypatch, cards, *round_arguments, command="round")
    assert "Voyager" not in capsys.readouterr().out


def test_a_failed_move_keeps_the_records_and_says_what_is_left(
    monkeypatch, tmp_path, capsys, notifications
):
    cards, reports = tmp_path / "cards", tmp_path / "reports"
    file_report(monkeypatch, reports)

    def refuse(pane_id, label):
        raise HerdrUnavailable("herdr did not move worker-pane")

    monkeypatch.setattr(handover_cli, "move_pane_to_new_tab", refuse)
    assert handover(monkeypatch, cards, reports) == 1
    assert records(reports)[0]["state"] == "handed-over"
    assert "herdr did not move worker-pane" in capsys.readouterr().err
