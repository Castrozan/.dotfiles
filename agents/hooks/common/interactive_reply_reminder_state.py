from __future__ import annotations

import json
import os
import re

DEFAULT_REMINDER_STATE_DIRECTORY = "/tmp"


def resolve_reminder_state_directory() -> str:
    return (
        os.environ.get("INTERACTIVE_REPLY_REMINDER_STATE_DIRECTORY")
        or DEFAULT_REMINDER_STATE_DIRECTORY
    )


def reminder_state_path_for_session(session_id: str) -> str:
    safe_session_id = re.sub(r"[^a-zA-Z0-9_-]+", "-", session_id or "unknown")
    return os.path.join(
        resolve_reminder_state_directory(),
        f"interactive-reply-reminder-{safe_session_id}.json",
    )


def load_reminder_state(state_path: str) -> dict:
    try:
        with open(state_path) as state_file:
            return json.loads(state_file.read())
    except (json.JSONDecodeError, OSError):
        return {}


def write_reminder_state(state_path: str, state: dict) -> None:
    staging_path = f"{state_path}.{os.getpid()}.staging"
    try:
        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        with open(staging_path, "w") as staging_file:
            staging_file.write(json.dumps(state))
        os.replace(staging_path, state_path)
    except OSError:
        try:
            os.remove(staging_path)
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
