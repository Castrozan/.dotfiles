import socket

import pytest
from hypothesis import given
from hypothesis import strategies as st
from orchestrator_cli.releases.released_sessions import (
    SessionIdentity,
    is_same_session,
)
from orchestrator_cli.watch import workspace_watch
from release_test_support import RELEASED_PANE, records


def test_what_a_released_session_files_is_refused_and_never_reaches_the_orchestrator(
    scenario,
):
    assert scenario.file_report(state="working") == 0
    assert scenario.handover() == 0
    scenario.notifications.clear()
    scenario.errors()
    assert scenario.file_report() == 1
    assert scenario.file_card() == 1
    refusals = scenario.errors()
    assert refusals.count("released this session to Lucas") == 2
    assert "Tell Lucas in your pane" in refusals
    assert scenario.notifications == [] and records(scenario.cards) == []
    assert [report["state"] for report in records(scenario.reports)] == ["handed-over"]
    assert "worker-session" not in scenario.round_output()


def test_a_release_follows_the_session_into_another_pane(scenario, live_panes):
    session = {"kind": "id", "value": "conversation-1"}
    live_panes[RELEASED_PANE] = {"pane_id": RELEASED_PANE, "agent_session": session}
    assert scenario.handover() == 0
    live_panes["wL:p4"] = {"pane_id": "wL:p4", "agent_session": session}
    scenario.monkeypatch.setenv("HERDR_PANE_ID", "wL:p4")
    assert scenario.file_report() == 1
    assert "released this session" in scenario.errors()


def test_another_session_still_files_while_a_release_stands(scenario, live_panes):
    assert scenario.handover() == 0
    scenario.notifications.clear()
    scenario.monkeypatch.setenv("HERDR_PANE_ID", "wW:p7")
    for pane in (None, {"pane_id": "wW:p7", "agent_session": None}):
        live_panes["wW:p7"] = pane
        assert scenario.file_report() == 0
        assert scenario.file_card() == 0
    assert len(scenario.notifications) == 3 and len(records(scenario.cards)) == 2


def blocked_event(pane):
    data = {"pane_id": pane, "workspace_id": "wW", "agent_status": "blocked"}
    return {"event": "pane.agent_status_changed", "data": data}


@pytest.fixture
def subscribed_sockets(monkeypatch):
    connections = []

    def subscribed(subscriptions):
        connections.extend(socket.socketpair())
        return connections[-1]

    monkeypatch.setattr(workspace_watch, "subscribed_socket", subscribed)
    yield connections
    for connection in connections:
        connection.close()


def test_a_released_session_prints_no_watch_event_and_no_timeout(
    scenario, monkeypatch, tmp_path, subscribed_sockets
):
    panes = [
        {"pane_id": pane, "agent": "claude", "agent_status": "idle"}
        for pane in (RELEASED_PANE, "wW:p2")
    ]
    monkeypatch.setattr(workspace_watch, "workspace_panes", lambda _: panes)
    followed = frozenset({RELEASED_PANE, "wW:p2"})
    watch = workspace_watch.WorkspaceWatch(
        workspace_watch.WatchConfiguration("wW", tmp_path, tmp_path, 15, followed, None)
    )
    assert watch.start() == [] and set(watch.sessions) == followed
    assert scenario.handover() == 0
    assert watch.line_from_message(blocked_event(RELEASED_PANE)) is None
    assert watch.line_from_message(blocked_event("wW:p2")) == "BLOCKED wW:p2"
    watch.timeout = -watch.timeout
    overdue = [line.split()[:2] for line in watch.check_timeouts()]
    assert overdue == [["TIMEOUT", "wW:p2"]]
    restarted = workspace_watch.WorkspaceWatch(watch.configuration)
    assert restarted.start() == [] and set(restarted.sessions) == {"wW:p2"}


identifiers = st.sampled_from(["a", "b", "c", "d"])
identities = st.builds(
    SessionIdentity,
    st.frozensets(identifiers, min_size=1),
    st.none() | identifiers,
)


@given(identities, identities)
def test_two_identities_are_one_session_when_they_share_a_pane_or_a_conversation(
    filer, released
):
    release = {
        "panes": sorted(released.panes),
        "session_identifier": released.session_identifier,
    }
    shares_conversation = (
        filer.session_identifier is not None
        and filer.session_identifier == released.session_identifier
    )
    assert is_same_session(filer, release) == (
        bool(filer.panes & released.panes) or shares_conversation
    )
