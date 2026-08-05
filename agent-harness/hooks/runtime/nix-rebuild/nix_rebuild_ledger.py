from __future__ import annotations

from session_scoped_path_ledger import (
    append_path_to_session_ledger,
    read_and_clear_session_ledger,
    session_ledger_path,
)

CHANGED_NIX_FILE_LEDGER_NAME = "nix-rebuild"


def ledger_file_path_for_session(session_id: str) -> str:
    return session_ledger_path(CHANGED_NIX_FILE_LEDGER_NAME, session_id)


def append_changed_nix_file(session_id: str, file_path: str) -> None:
    append_path_to_session_ledger(CHANGED_NIX_FILE_LEDGER_NAME, session_id, file_path)


def read_and_clear_changed_nix_files(session_id: str) -> list[str]:
    return read_and_clear_session_ledger(CHANGED_NIX_FILE_LEDGER_NAME, session_id)
