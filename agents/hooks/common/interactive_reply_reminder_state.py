from __future__ import annotations

import json
import os
import re
from pathlib import Path


def resolve_reminder_state_directory() -> Path:
    override = os.environ.get("INTERACTIVE_REPLY_REMINDER_STATE_DIRECTORY")
    if override:
        return Path(override)
    return Path("/tmp")


def reminder_state_path_for_session(session_id: str) -> Path:
    safe_session_id = re.sub(r"[^a-zA-Z0-9_-]+", "-", session_id or "unknown")
    return (
        resolve_reminder_state_directory()
        / f"interactive-reply-reminder-{safe_session_id}.json"
    )


def load_reminder_state(state_path: Path) -> dict:
    if not state_path.exists():
        return {}
    try:
        return json.loads(state_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def write_reminder_state(state_path: Path, state: dict) -> None:
    staging_path = state_path.with_name(f"{state_path.name}.{os.getpid()}.staging")
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        staging_path.write_text(json.dumps(state))
        os.replace(staging_path, state_path)
    except OSError:
        try:
            staging_path.unlink()
        except OSError:
            pass


def reply_reminder_should_be_injected(session_id: str) -> bool:
    state = load_reminder_state(reminder_state_path_for_session(session_id))
    if not state.get("reminder_has_been_injected_this_session", False):
        return True
    return state.get("rearm_requested_after_drift", False)


def record_reply_reminder_injected(session_id: str) -> None:
    state_path = reminder_state_path_for_session(session_id)
    state = load_reminder_state(state_path)
    state["reminder_has_been_injected_this_session"] = True
    state["rearm_requested_after_drift"] = False
    write_reminder_state(state_path, state)


def request_reply_reminder_rearm_after_drift(session_id: str) -> None:
    state_path = reminder_state_path_for_session(session_id)
    state = load_reminder_state(state_path)
    state["rearm_requested_after_drift"] = True
    write_reminder_state(state_path, state)
