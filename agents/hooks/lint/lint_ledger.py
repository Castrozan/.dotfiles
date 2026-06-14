from __future__ import annotations

import os
import tempfile


def ledger_file_path_for_session(session_id: str) -> str:
    safe_session_id = session_id or "unknown-session"
    return os.path.join(
        tempfile.gettempdir(), f"claude-lint-ledger-{safe_session_id}.txt"
    )


def append_edited_source_file(session_id: str, file_path: str) -> None:
    try:
        with open(ledger_file_path_for_session(session_id), "a") as ledger_file:
            ledger_file.write(file_path + "\n")
    except OSError:
        pass


def read_and_clear_edited_source_files(session_id: str) -> list[str]:
    ledger_path = ledger_file_path_for_session(session_id)
    try:
        with open(ledger_path) as ledger_file:
            recorded_paths = [line.strip() for line in ledger_file if line.strip()]
    except OSError:
        return []
    try:
        os.remove(ledger_path)
    except OSError:
        pass
    deduplicated_paths: list[str] = []
    already_seen: set[str] = set()
    for recorded_path in recorded_paths:
        if recorded_path not in already_seen:
            already_seen.add(recorded_path)
            deduplicated_paths.append(recorded_path)
    return deduplicated_paths
