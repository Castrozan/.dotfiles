import json
from pathlib import Path

import pytest
from orchestrator_cli.watch import herdr_events

from orchestrator_cli.watch.herdr_events import decoded_messages
from orchestrator_cli.watch.workspace_watch import event_line


def status_event(status, workspace="wW", pane="wW:p1"):
    return {
        "event": "pane.agent_status_changed",
        "data": {
            "pane_id": pane,
            "workspace_id": workspace,
            "agent_status": status,
            "title": "drop codex patch",
        },
    }


def test_attention_states_become_lines_and_working_stays_silent():
    assert event_line(status_event("blocked"), "wW") == (
        "BLOCKED wW:p1 drop codex patch",
        None,
    )
    assert event_line(status_event("done"), "wW")[0] == "DONE wW:p1 drop codex patch"
    assert event_line(status_event("working"), "wW") == (None, None)


def test_events_from_other_workspaces_are_ignored_and_new_agents_are_followed():
    assert event_line(status_event("blocked", workspace="wX"), "wW") == (None, None)
    detected = {
        "event": "pane.agent_detected",
        "data": {"pane_id": "wW:p2", "workspace_id": "wW"},
    }
    assert event_line(detected, "wW") == ("STARTED wW:p2", "wW:p2")


def test_partial_socket_lines_wait_for_their_newline():
    first = json.dumps(status_event("done")).encode()
    messages, remainder = decoded_messages(first[:10])
    assert (messages, remainder) == ([], first[:10])
    messages, remainder = decoded_messages(remainder + first[10:] + b"\n")
    assert messages == [status_event("done")] and remainder == b""


@pytest.mark.parametrize(
    "environment,expected",
    [
        ({"HERDR_SOCKET_PATH": "/run/explicit.sock"}, "/run/explicit.sock"),
        ({"HERDR_SESSION": "work"}, "~/.config/herdr/sessions/work/herdr.sock"),
        ({}, "~/.config/herdr/herdr.sock"),
    ],
)
def test_the_socket_resolves_like_herdr_so_the_watch_runs_over_ssh(
    monkeypatch, environment, expected
):
    for variable in ("HERDR_SOCKET_PATH", "HERDR_SESSION"):
        monkeypatch.delenv(variable, raising=False)
    for variable, value in environment.items():
        monkeypatch.setenv(variable, value)
    assert herdr_events.herdr_socket_path() == Path(expected).expanduser()


def test_an_unreachable_socket_is_reported_instead_of_crashing(monkeypatch, tmp_path):
    monkeypatch.setenv("HERDR_SOCKET_PATH", str(tmp_path / "missing.sock"))
    with pytest.raises(herdr_events.HerdrUnavailable, match="missing.sock"):
        herdr_events.subscribed_socket([])
