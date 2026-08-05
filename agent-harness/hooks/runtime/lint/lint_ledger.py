from __future__ import annotations

from session_scoped_path_ledger import (
    append_path_to_session_ledger,
    read_and_clear_session_ledger,
    session_ledger_path,
)

EDITED_SOURCE_FILE_LEDGER_NAME = "lint"


def ledger_file_path_for_session(session_id: str) -> str:
    return session_ledger_path(EDITED_SOURCE_FILE_LEDGER_NAME, session_id)


def append_edited_source_file(session_id: str, file_path: str) -> None:
    append_path_to_session_ledger(EDITED_SOURCE_FILE_LEDGER_NAME, session_id, file_path)


def read_and_clear_edited_source_files(session_id: str) -> list[str]:
    return read_and_clear_session_ledger(EDITED_SOURCE_FILE_LEDGER_NAME, session_id)
