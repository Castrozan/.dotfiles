import json

from a2a_cli.watch.herdr_events import decoded_messages
from a2a_cli.watch.workspace_watch import event_line, stale_report_lines


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


def test_the_safety_net_names_only_working_reports_of_watched_panes_gone_quiet(
    tmp_path,
):
    reports = {
        "quiet": ("wW:p1", "working", "2000-01-01T00:00:00+00:00"),
        "blocked": ("wW:p1", "blocked", "2000-01-01T00:00:00+00:00"),
        "elsewhere": ("wX:p9", "working", "2000-01-01T00:00:00+00:00"),
        "fresh": ("wW:p2", "working", "2999-01-01T00:00:00+00:00"),
    }
    for name, (pane, state, updated_at) in reports.items():
        record = {
            "name": name,
            "requester_pane": pane,
            "state": state,
            "updated_at": updated_at,
        }
        (tmp_path / f"{name}.json").write_text(json.dumps(record))
    lines = stale_report_lines(tmp_path, {"wW:p1", "wW:p2"}, safety_minutes=30)
    assert lines == ["STALE quiet working since 2000-01-01T00:00:00+00:00"]
