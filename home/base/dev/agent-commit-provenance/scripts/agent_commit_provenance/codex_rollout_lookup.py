import json
import time
from pathlib import Path

CODEX_SESSIONS_DIRECTORY = Path.home() / ".codex" / "sessions"
MAXIMUM_ROLLOUT_AGE_SECONDS = 6 * 60 * 60
SESSION_META_RECORD_TYPE = "session_meta"


def rollout_session_identifier_when_working_directory_matches(
    rollout_path: Path, working_directory: Path
) -> str | None:
    try:
        with rollout_path.open(encoding="utf-8") as rollout_file:
            first_record_line = rollout_file.readline()
        first_record = json.loads(first_record_line)
    except (OSError, json.JSONDecodeError):
        return None
    if first_record.get("type") != SESSION_META_RECORD_TYPE:
        return None
    payload = first_record.get("payload")
    if not isinstance(payload, dict):
        return None
    if payload.get("cwd") != str(working_directory):
        return None
    session_identifier = payload.get("id")
    return session_identifier if isinstance(session_identifier, str) else None


def recently_modified_rollout_paths(
    sessions_directory: Path, current_time: float
) -> list[Path]:
    oldest_acceptable_modification_time = current_time - MAXIMUM_ROLLOUT_AGE_SECONDS
    rollout_paths_with_modification_times = []
    for rollout_path in sessions_directory.rglob("rollout-*.jsonl"):
        try:
            modification_time = rollout_path.stat().st_mtime
        except OSError:
            continue
        if modification_time >= oldest_acceptable_modification_time:
            rollout_paths_with_modification_times.append(
                (modification_time, rollout_path)
            )
    rollout_paths_with_modification_times.sort(reverse=True)
    return [
        rollout_path for _time, rollout_path in rollout_paths_with_modification_times
    ]


def codex_session_identifier_for_working_directory(
    working_directory: Path,
    sessions_directory: Path = CODEX_SESSIONS_DIRECTORY,
    current_time: float | None = None,
) -> str | None:
    if not sessions_directory.is_dir():
        return None
    for rollout_path in recently_modified_rollout_paths(
        sessions_directory, current_time if current_time is not None else time.time()
    ):
        session_identifier = rollout_session_identifier_when_working_directory_matches(
            rollout_path, working_directory
        )
        if session_identifier is not None:
            return session_identifier
    return None
