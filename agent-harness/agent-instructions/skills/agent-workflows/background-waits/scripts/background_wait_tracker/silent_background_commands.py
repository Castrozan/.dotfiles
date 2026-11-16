from __future__ import annotations

import os
from dataclasses import dataclass

NOTIFIED_LATE = "notified-late"
STOPPED_BY_AGENT = "stopped-by-agent"
REPORTED_STILL_RUNNING = "reported-still-running"


@dataclass(frozen=True)
class ProvenSilence:
    seconds: float
    outcome: str


def _first_notification_precedes_any_stop(run):
    if not run.first_notified_at:
        return False
    return (
        run.stopped_by_agent_at is None
        or run.first_notified_at < run.stopped_by_agent_at
    )


def proven_silence_of(run):
    if run.denied_reason or run.task_id is None:
        return None
    if _first_notification_precedes_any_stop(run):
        silence_end, outcome = run.first_notified_at, NOTIFIED_LATE
    elif run.stopped_by_agent_at or run.last_seen_running_at:
        silence_end, outcome = max(
            (proof_time, proof_outcome)
            for proof_time, proof_outcome in (
                (run.stopped_by_agent_at, STOPPED_BY_AGENT),
                (run.last_seen_running_at, REPORTED_STILL_RUNNING),
            )
            if proof_time
        )
    else:
        return None
    return ProvenSilence(
        seconds=(silence_end - run.launched_at).total_seconds(), outcome=outcome
    )


def _output_bytes_still_on_disk(output_file_path):
    if not output_file_path or not os.path.isfile(output_file_path):
        return None
    return os.path.getsize(output_file_path)


def silent_command_record(run, transcript_path, minimum_silent_seconds):
    silence = proven_silence_of(run)
    if silence is None or silence.seconds < minimum_silent_seconds:
        return None
    return {
        "id": run.tool_use_id,
        "tool_name": run.tool_name,
        "command": run.command,
        "launched_at": run.launched_at.isoformat(),
        "silent_minutes": int(silence.seconds // 60),
        "outcome": silence.outcome,
        "output_bytes": _output_bytes_still_on_disk(run.output_file_path),
        "transcript_path": str(transcript_path),
        "dismissed_reason": None,
    }
