import json

import pytest
from background_wait_tracker import __main__ as tracker_cli
from transcript_fixture import (
    INCIDENT_COMMAND,
    launch_record,
    started_record,
    task_stop_record,
    write_transcript,
)

STUCK_REMOTE_POLL = (
    "for i in $(seq 1 60); do curl -sf https://api.example.com/job | grep -q done "
    "&& break; sleep 30; done"
)


@pytest.fixture
def ledger_path(tmp_path):
    return tmp_path / "state" / "silent-background-commands.jsonl"


@pytest.fixture
def transcript_path(tmp_path):
    return write_transcript(
        tmp_path / "session.jsonl",
        [
            launch_record("toolu_incident", INCIDENT_COMMAND),
            started_record("toolu_incident", "task_incident"),
            task_stop_record("task_incident", minutes_after_launch=170),
            launch_record("toolu_remote_poll", STUCK_REMOTE_POLL),
            started_record("toolu_remote_poll", "task_remote_poll"),
            task_stop_record("task_remote_poll", minutes_after_launch=95),
        ],
    )


def run_tracker(monkeypatch, capsys, ledger_path, *arguments):
    monkeypatch.setattr(
        "sys.argv",
        ["background-wait-tracker", "--ledger", str(ledger_path), *arguments],
    )
    exit_code = tracker_cli.main()
    return exit_code, capsys.readouterr().out


def test_a_replayed_incident_is_recorded_and_reads_as_denied_now(
    monkeypatch, capsys, ledger_path, transcript_path
):
    exit_code, scan_output = run_tracker(
        monkeypatch, capsys, ledger_path, "scan", "--transcript", str(transcript_path)
    )
    assert exit_code == 0
    assert "2 silent commands, 2 new" in scan_output

    _exit_code, show_output = run_tracker(
        monkeypatch, capsys, ledger_path, "show", "toolu_incident"
    )
    incident_record = json.loads(show_output)
    assert incident_record["command"] == INCIDENT_COMMAND
    assert incident_record["silent_minutes"] == 170
    assert incident_record["denied_now_by"] == ["sleep-paced-loop"]


def test_the_listing_holds_only_silent_commands_still_allowed_and_undismissed(
    monkeypatch, capsys, ledger_path, transcript_path
):
    run_tracker(
        monkeypatch, capsys, ledger_path, "scan", "--transcript", str(transcript_path)
    )

    _exit_code, listing = run_tracker(monkeypatch, capsys, ledger_path, "list")
    assert [line.split("\t")[0] for line in listing.splitlines()] == [
        "toolu_remote_poll"
    ]
    assert "allowed:remote-state-safety-net" in listing

    run_tracker(
        monkeypatch,
        capsys,
        ledger_path,
        "dismiss",
        "toolu_remote_poll",
        "--reason",
        "activation was merely slow",
    )
    _exit_code, listing_after_dismissal = run_tracker(
        monkeypatch, capsys, ledger_path, "list"
    )
    assert listing_after_dismissal == ""


def test_a_second_scan_keeps_the_dismissal_and_records_nothing_new(
    monkeypatch, capsys, ledger_path, transcript_path
):
    scan_arguments = ("scan", "--transcript", str(transcript_path))
    run_tracker(monkeypatch, capsys, ledger_path, *scan_arguments)
    run_tracker(
        monkeypatch,
        capsys,
        ledger_path,
        "dismiss",
        "toolu_remote_poll",
        "--reason",
        "slow",
    )

    _exit_code, second_scan_output = run_tracker(
        monkeypatch, capsys, ledger_path, *scan_arguments
    )
    _exit_code, full_listing = run_tracker(
        monkeypatch, capsys, ledger_path, "list", "--all", "--json"
    )

    assert "0 new" in second_scan_output
    dismissed_reason_by_id = {
        record["id"]: record["dismissed_reason"] for record in json.loads(full_listing)
    }
    assert dismissed_reason_by_id == {
        "toolu_incident": None,
        "toolu_remote_poll": "slow",
    }


def test_an_unknown_record_is_reported_as_an_error(monkeypatch, capsys, ledger_path):
    exit_code, _output = run_tracker(
        monkeypatch, capsys, ledger_path, "dismiss", "toolu_missing", "--reason", "x"
    )
    assert exit_code == 1
