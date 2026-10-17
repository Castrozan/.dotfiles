from __future__ import annotations

import os

from hook_state_directory import hook_state_directory

UNIDENTIFIED_SESSION = "unknown-session"


def temporary_directory() -> str:
    return str(hook_state_directory())


def session_ledger_path(ledger_name: str, session_id: str) -> str:
    return os.path.join(
        temporary_directory(),
        f"claude-{ledger_name}-ledger-{session_id or UNIDENTIFIED_SESSION}.txt",
    )


def append_path_to_session_ledger(
    ledger_name: str, session_id: str, file_path: str
) -> None:
    try:
        with open(session_ledger_path(ledger_name, session_id), "a") as ledger_file:
            ledger_file.write(file_path + "\n")
    except OSError:
        pass


def read_and_clear_session_ledger(ledger_name: str, session_id: str) -> list[str]:
    ledger_path = session_ledger_path(ledger_name, session_id)
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
