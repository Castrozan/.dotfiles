import os
import time

from background_wait_tracker.transcript_discovery import (
    recent_transcripts_launching_background_commands,
)
from transcript_fixture import INCIDENT_COMMAND, launch_record, write_transcript

SECONDS_PER_DAY = 86400


def age_file(file_path, days_old):
    aged_time = time.time() - days_old * SECONDS_PER_DAY
    os.utime(file_path, (aged_time, aged_time))


def test_only_recent_transcripts_that_launch_background_commands_are_found(tmp_path):
    project_directory = tmp_path / "project" / "subagents"
    project_directory.mkdir(parents=True)
    recent_background_launch = write_transcript(
        project_directory / "recent-background.jsonl",
        [launch_record("toolu_recent", INCIDENT_COMMAND)],
    )
    recent_monitor_launch = write_transcript(
        tmp_path / "project" / "recent-monitor.jsonl",
        [launch_record("toolu_monitor", "tail -f /var/log/app.log", "Monitor")],
    )
    stale_background_launch = write_transcript(
        tmp_path / "project" / "stale-background.jsonl",
        [launch_record("toolu_stale", INCIDENT_COMMAND)],
    )
    age_file(stale_background_launch, days_old=30)
    (tmp_path / "project" / "foreground-only.jsonl").write_text(
        '{"type":"assistant","message":{"content":[{"type":"tool_use",'
        '"name":"Bash","input":{"command":"ls"}}]}}\n'
    )
    (tmp_path / "project" / "empty.jsonl").write_text("")
    (tmp_path / "project" / "notes.txt").write_text('"run_in_background":true')

    found = recent_transcripts_launching_background_commands(tmp_path, since_days=7)

    assert sorted(found) == sorted(
        [str(recent_background_launch), str(recent_monitor_launch)]
    )
