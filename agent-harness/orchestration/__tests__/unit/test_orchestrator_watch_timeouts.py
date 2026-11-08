import json
import socket
from datetime import datetime, timedelta, timezone

import pytest
from orchestrator_cli.watch import workspace_watch

BEGINNING = datetime(2026, 11, 8, 9, 0, tzinfo=timezone.utc)


class WatchHarness:
    def __init__(self, monkeypatch, tmp_path, panes, followed=frozenset(), own=None):
        self.now = BEGINNING
        self.sockets = []
        self.watch_ends = []
        monkeypatch.setattr(workspace_watch, "current_time", lambda: self.now)
        monkeypatch.setattr(workspace_watch, "workspace_agent_panes", lambda _: panes)
        monkeypatch.setattr(workspace_watch, "subscribed_socket", self.subscribed)
        self.reports = tmp_path / "reports"
        self.decisions = tmp_path / "decisions"
        self.reports.mkdir()
        self.decisions.mkdir()
        self.watch = workspace_watch.WorkspaceWatch(
            workspace_watch.WatchConfiguration(
                "wW", self.reports, self.decisions, 15, followed, own
            )
        )
        self.watch.start()
        assert self.watch.next_lines() == []

    def subscribed(self, subscriptions):
        herdr_end, watch_end = socket.socketpair()
        self.sockets.append(herdr_end)
        self.watch_ends.append(watch_end)
        return watch_end

    def advance(self, minutes):
        self.now += timedelta(minutes=minutes)

    def emit(self, event, pane, **fields):
        message = {
            "event": event,
            "data": {"pane_id": pane, "workspace_id": "wW", **fields},
        }
        self.sockets[0].sendall((json.dumps(message) + "\n").encode())
        return self.watch.next_lines()

    def write_report(self, pane, state):
        report = {
            "name": "voyager",
            "requester_pane": pane,
            "state": state,
            "updated_at": self.now.isoformat(),
        }
        (self.reports / "voyager.json").write_text(json.dumps(report))

    def close(self):
        for connection in self.sockets + self.watch_ends:
            connection.close()


@pytest.fixture
def harness(monkeypatch, tmp_path):
    created = []

    def build(panes, **options):
        created.append(WatchHarness(monkeypatch, tmp_path, panes, **options))
        return created[-1]

    yield build
    for each in created:
        each.close()


def idle_pane(pane_id):
    return {"pane_id": pane_id, "agent": "claude", "agent_status": "idle"}


STATUS_CHANGED = "pane.agent_status_changed"


def test_a_silent_idle_session_keeps_timing_out_until_it_answers(harness):
    watch = harness([idle_pane("wW:p1")])
    watch.advance(14)
    assert watch.watch.check_timeouts() == []
    watch.advance(1)
    assert watch.watch.next_lines() == [
        "TIMEOUT wW:p1 idle quiet-minutes=15 report=none"
    ]
    watch.advance(14)
    assert watch.watch.check_timeouts() == []
    watch.advance(1)
    assert watch.watch.next_lines() == [
        "TIMEOUT wW:p1 idle quiet-minutes=30 report=none"
    ]
    watch.write_report("wW:p1", "working")
    watch.advance(14)
    assert watch.watch.check_timeouts() == []


def test_each_session_runs_its_own_clock(harness):
    watch = harness([idle_pane("wW:p1"), idle_pane("wW:p2")])
    watch.advance(10)
    assert watch.emit(STATUS_CHANGED, "wW:p2", agent_status="working") == []
    watch.advance(5)
    assert watch.watch.next_lines() == [
        "TIMEOUT wW:p1 idle quiet-minutes=15 report=none"
    ]
    watch.advance(10)
    assert watch.watch.next_lines() == [
        "TIMEOUT wW:p2 working quiet-minutes=15 report=none"
    ]


def test_a_finished_session_stays_silent_until_it_is_given_more_work(harness):
    watch = harness([idle_pane("wW:p1")])
    watch.write_report("wW:p1", "done")
    watch.advance(60)
    assert watch.watch.check_timeouts() == []
    assert watch.emit(STATUS_CHANGED, "wW:p1", agent_status="working") == []
    watch.advance(15)
    assert watch.watch.next_lines() == [
        "TIMEOUT wW:p1 working quiet-minutes=15 report=done"
    ]


def test_an_exited_session_stops_timing_out(harness):
    watch = harness([idle_pane("wW:p1")])
    assert watch.emit("pane.exited", "wW:p1") == ["EXITED wW:p1"]
    watch.advance(60)
    assert watch.watch.check_timeouts() == []


def test_a_restarted_watch_resumes_from_the_durable_answer_time(harness):
    first = harness([idle_pane("wW:p1")])
    first.write_report("wW:p1", "working")
    first.advance(40)
    restarted = workspace_watch.WorkspaceWatch(
        workspace_watch.WatchConfiguration(
            "wW", first.reports, first.decisions, 15, frozenset(), None
        )
    )
    restarted.start()
    assert restarted.next_lines() == [
        "TIMEOUT wW:p1 idle quiet-minutes=40 report=working"
    ]


def test_the_watch_skips_its_own_pane_and_panes_it_was_not_asked_to_follow(harness):
    panes = [idle_pane("wW:p1"), idle_pane("wW:p2"), idle_pane("wW:p3")]
    watch = harness(panes, followed=frozenset({"wW:p1", "wW:p2"}), own="wW:p2")
    assert set(watch.watch.sessions) == {"wW:p1"}
    assert watch.emit("pane.agent_detected", "wW:p3") == []
    assert watch.emit("pane.exited", "wW:p2") == []
    assert set(watch.watch.sessions) == {"wW:p1"}
