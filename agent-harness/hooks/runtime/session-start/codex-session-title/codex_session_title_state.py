from __future__ import annotations

import hashlib
import os
from pathlib import Path


def generated_session_title_state_path(thread_identifier: str) -> Path:
    state_directory = Path(
        os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state"
    )
    thread_digest = hashlib.sha256(thread_identifier.encode()).hexdigest()
    return state_directory / "dotfiles" / "codex-session-titles" / thread_digest


def generated_session_title_is_current(
    thread_identifier: str, name_digest: str
) -> bool:
    try:
        stored_digest = generated_session_title_state_path(
            thread_identifier
        ).read_text()
    except OSError:
        return False
    return stored_digest == name_digest


def record_generated_session_title(thread_identifier: str, name_digest: str) -> None:
    state_path = generated_session_title_state_path(thread_identifier)
    state_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    state_path.write_text(name_digest)
