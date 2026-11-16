import json

import pytest
from background_wait_tracker.silent_background_commands import (
    NOTIFIED_LATE,
    REPORTED_STILL_RUNNING,
    STOPPED_BY_AGENT,
    silent_command_record,
)
from background_wait_tracker.transcript_background_runs import (
    background_command_runs_in_transcript,
)
from transcript_fixture import (
    INCIDENT_COMMAND,
    completion_notification_record,
    denied_record,
    launch_record,
    monitor_event_record,
    started_record,
    still_running_record,
    task_stop_record,
    write_transcript,
)

THIRTY_MINUTES_IN_SECONDS = 1800


def silent_records_in(transcript_path):
    return [
        record
        for run in background_command_runs_in_transcript(transcript_path)
        if (
            record := silent_command_record(
                run, transcript_path, THIRTY_MINUTES_IN_SECONDS
            )
        )
    ]


def test_the_incident_wait_stopped_after_hours_is_recorded(tmp_path):
    transcript_path = write_transcript(
        tmp_path / "session.jsonl",
        [
            launch_record("toolu_incident", INCIDENT_COMMAND),
            started_record("toolu_incident", "bstinl0za"),
            task_stop_record("bstinl0za", minutes_after_launch=170),
        ],
    )

    (record,) = silent_records_in(transcript_path)

    assert record["id"] == "toolu_incident"
    assert record["command"] == INCIDENT_COMMAND
    assert record["outcome"] == STOPPED_BY_AGENT
    assert record["silent_minutes"] == 170
    assert record["dismissed_reason"] is None


def test_a_wait_the_harness_reports_still_running_is_recorded(tmp_path):
    transcript_path = write_transcript(
        tmp_path / "session.jsonl",
        [
            launch_record("toolu_running", INCIDENT_COMMAND),
            started_record("toolu_running", "task1"),
            still_running_record("task1", minutes_after_launch=158),
        ],
    )

    (record,) = silent_records_in(transcript_path)

    assert record["outcome"] == REPORTED_STILL_RUNNING
    assert record["silent_minutes"] == 158


@pytest.mark.parametrize(
    ("minutes_until_notification", "expected_outcomes"),
    [(29, []), (30, [NOTIFIED_LATE]), (199, [NOTIFIED_LATE])],
)
def test_a_wait_is_recorded_only_when_its_first_notification_comes_late(
    tmp_path, minutes_until_notification, expected_outcomes
):
    transcript_path = write_transcript(
        tmp_path / "session.jsonl",
        [
            launch_record("toolu_poll", "until [ -f /tmp/done ]; do sleep 5; done"),
            started_record("toolu_poll", "task1"),
            completion_notification_record(
                "toolu_poll", "task1", minutes_until_notification
            ),
            task_stop_record("task1", minutes_after_launch=400),
        ],
    )

    assert [
        record["outcome"] for record in silent_records_in(transcript_path)
    ] == expected_outcomes


def test_a_monitor_event_counts_as_the_first_notification(tmp_path):
    transcript_path = write_transcript(
        tmp_path / "session.jsonl",
        [
            launch_record(
                "toolu_monitor", "orchestrator watch --workspace w4E", "Monitor"
            ),
            started_record("toolu_monitor", "monitor1"),
            monitor_event_record("monitor1", minutes_after_launch=4),
            task_stop_record("monitor1", minutes_after_launch=300),
        ],
    )

    assert silent_records_in(transcript_path) == []


def test_a_denied_launch_never_ran_and_is_not_recorded(tmp_path):
    transcript_path = write_transcript(
        tmp_path / "session.jsonl",
        [
            launch_record("toolu_denied", INCIDENT_COMMAND),
            denied_record(
                "toolu_denied", "background wait outside the known-good shapes"
            ),
            task_stop_record("bstinl0za", minutes_after_launch=170),
        ],
    )

    assert silent_records_in(transcript_path) == []


def test_a_launch_with_no_later_proof_of_running_is_not_recorded(tmp_path):
    transcript_path = write_transcript(
        tmp_path / "session.jsonl",
        [
            launch_record("toolu_unproven", INCIDENT_COMMAND),
            started_record("toolu_unproven", "task1"),
        ],
    )

    assert silent_records_in(transcript_path) == []


def test_request_copies_and_malformed_lines_are_skipped(tmp_path):
    transcript_path = tmp_path / "session.jsonl"
    launch = launch_record("toolu_incident", INCIDENT_COMMAND)
    request_copy = {"type": "api-request-blob", "message": launch["message"]}
    transcript_path.write_text(
        "\n".join(
            [
                json.dumps(launch, separators=(",", ":")),
                json.dumps(request_copy, separators=(",", ":")),
                "{truncated",
                json.dumps(started_record("toolu_incident", "task1")),
                json.dumps(task_stop_record("task1", minutes_after_launch=45)),
            ]
        )
        + "\n"
    )

    assert [
        record["silent_minutes"] for record in silent_records_in(transcript_path)
    ] == [45]
