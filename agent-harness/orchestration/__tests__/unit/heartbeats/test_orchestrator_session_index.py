import itertools
import subprocess

import pytest
from orchestration_test_support import run_orchestrator
from orchestrator_cli.heartbeats.session_index import entries_of
from orchestrator_cli.heartbeats.status import SessionStatus, pane_flags
from orchestrator_cli.watch import herdr_events
from session_index_test_support import (
    ORCHESTRATOR,
    age_heartbeat,
    close_session,
    dispatch,
    file_heartbeat,
    heartbeats_directory,
    open_row,
    status_output,
)

VOYAGER = "Voyager-wW-p4"
MOZART = "Mozart-kira-w1-p2"


def test_dispatch_indexes_the_session_and_its_heartbeat_lands_where_the_index_points(
    monkeypatch, tmp_path, capsys, notifications
):
    assert dispatch(monkeypatch, tmp_path, "Voyager") == 0
    assert capsys.readouterr().out.strip().endswith(f"indexed as {VOYAGER}")
    (entry,) = entries_of(ORCHESTRATOR)
    assert entry["goal"] == "Hey-bot is gone and the avatar answers its wake word."
    assert entry["brief"] == str(tmp_path / "brief.md")
    monkeypatch.setenv("HERDR_PANE_ID", "wW:p4")
    assert file_heartbeat(monkeypatch) == 0
    assert entries_of(ORCHESTRATOR)[0]["heartbeat"] == str(
        heartbeats_directory() / f"{VOYAGER}.json"
    )
    assert (heartbeats_directory() / f"{VOYAGER}.json").is_file()


def test_a_remote_session_files_by_its_name_into_the_entry_dispatch_made(
    monkeypatch, tmp_path, capsys, notifications
):
    assert dispatch(monkeypatch, tmp_path, "Mozart", "--host", "kira") == 0
    monkeypatch.delenv("HERDR_PANE_ID")
    assert (
        file_heartbeat(monkeypatch, "--sender", "Mozart", "--reply-host", "kira") == 0
    )
    assert capsys.readouterr().out.strip().endswith(MOZART)
    row = open_row(status_output(monkeypatch, capsys, {}), MOZART)
    assert "| working | on kira | 0m ago |" in row and row.endswith("| none |")


def test_a_redispatch_keeps_one_entry_and_close_moves_it_to_the_closed_part(
    monkeypatch, tmp_path, capsys, notifications
):
    dispatch(monkeypatch, tmp_path, "Voyager")
    dispatch(monkeypatch, tmp_path, "wW:p4")
    assert [entry["name"] for entry in entries_of(ORCHESTRATOR)] == [VOYAGER]
    assert close_session(monkeypatch, "Ghost") == 1
    assert "no session in the index is called Ghost" in capsys.readouterr().err
    assert close_session(monkeypatch, "voyager") == 0
    assert close_session(monkeypatch, VOYAGER) == 1
    output = status_output(monkeypatch, capsys, {"wW:p4": "idle"})
    assert "No session is open." in output
    assert f"| {VOYAGER} |" in output.split("### Closed sessions")[1]
    assert f"- {VOYAGER}: {heartbeats_directory() / f'{VOYAGER}.json'}" in output


def test_status_flags_a_stale_heartbeat_an_idle_pane_and_a_silent_dispatch(
    monkeypatch, tmp_path, capsys, notifications
):
    dispatch(monkeypatch, tmp_path, "Voyager")
    monkeypatch.setenv("HERDR_PANE_ID", "wW:p4")
    file_heartbeat(monkeypatch, doing="porting the wake word")
    age_heartbeat(VOYAGER, 40)
    row = open_row(status_output(monkeypatch, capsys, {"wW:p4": "idle"}), VOYAGER)
    assert "porting the wake word" in row
    assert row.endswith("| stale 40m, pane idle while working |")
    file_heartbeat(monkeypatch, state="waiting", doing="waiting on the nix build")
    row = open_row(status_output(monkeypatch, capsys, {"wW:p4": "idle"}), VOYAGER)
    assert row.endswith("| none |")
    file_heartbeat(monkeypatch, state="waiting")
    row = open_row(status_output(monkeypatch, capsys, {"wW:p4": "gone"}), VOYAGER)
    assert row.endswith("| pane gone |")


def test_a_dispatched_session_that_never_publishes_is_flagged_after_the_bound(
    monkeypatch, tmp_path, capsys, notifications
):
    dispatch(monkeypatch, tmp_path, "Voyager")
    row = open_row(status_output(monkeypatch, capsys, {"wW:p4": "idle"}), VOYAGER)
    assert "| no heartbeat | idle | never | goal: Hey-bot is gone" in row
    assert row.endswith("| pane idle while no heartbeat |")


STATES = ["working", "waiting", "blocked", "done", "handed-over", None]
PANE_STATUSES = ["working", "idle", "done", "blocked", "gone", "unknown", "on kira"]


@pytest.mark.parametrize(
    ("state", "pane_status"), itertools.product(STATES, PANE_STATUSES)
)
def test_a_pane_is_flagged_only_when_it_contradicts_the_heartbeat(state, pane_status):
    heartbeat = {"state": state} if state else None
    flagged = bool(pane_flags(SessionStatus({}, heartbeat, pane_status)))
    contradicts = {
        "working": {"idle", "done", "blocked"},
        None: {"idle", "done", "blocked"},
        "waiting": {"blocked"},
    }.get(state, set())
    assert flagged == (pane_status == "gone" or pane_status in contradicts)


@pytest.mark.parametrize(
    ("reply", "status"),
    [
        ({"error": {"code": "pane_not_found"}}, "gone"),
        ({"result": {"pane": {"pane_id": "wW:p4", "agent": None}}}, "gone"),
        ({"result": {"pane": {"agent": "claude", "agent_status": "idle"}}}, "idle"),
        ({"result": {"pane": {"agent": "claude"}}}, "unknown"),
        ({}, "unknown"),
    ],
)
def test_herdr_replies_map_to_one_pane_status(monkeypatch, reply, status):
    monkeypatch.setattr(herdr_events, "pane_reply", lambda pane_id: reply)
    assert herdr_events.pane_agent_status("wW:p4") == status


def test_herdr_reports_a_missing_pane_on_stderr_and_it_reads_as_gone(monkeypatch):
    missing = '{"error":{"code":"pane_not_found","message":"pane wZ:p9 not found"}}'
    completed = subprocess.CompletedProcess([], 1, stdout="", stderr=missing)
    monkeypatch.setattr(herdr_events.subprocess, "run", lambda *_, **__: completed)
    assert herdr_events.pane_agent_status("wZ:p9") == "gone"


def test_a_closed_session_leaves_the_round(
    monkeypatch, tmp_path, capsys, notifications
):
    dispatch(monkeypatch, tmp_path, "Voyager")
    monkeypatch.setenv("HERDR_PANE_ID", "wW:p4")
    file_heartbeat(monkeypatch)
    round_arguments = ["--heartbeats-dir", str(heartbeats_directory())]
    options = dict(command="round", location_flag="--dir")
    run_orchestrator(monkeypatch, tmp_path / "cards", *round_arguments, **options)
    assert VOYAGER in capsys.readouterr().out
    close_session(monkeypatch, VOYAGER)
    capsys.readouterr()
    run_orchestrator(monkeypatch, tmp_path / "cards", *round_arguments, **options)
    assert VOYAGER not in capsys.readouterr().out
