#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

CODEX_AGENT_NAME = "codex"
CODEX_REPORT_SOURCE = "herdr:codex"
SESSION_META_RECORD_TYPE = "session_meta"


def agent_information_from_response(agent_get_response: dict) -> dict | None:
    result = agent_get_response.get("result")
    if not isinstance(result, dict):
        return None
    agent_information = result.get("agent")
    return agent_information if isinstance(agent_information, dict) else None


def _is_codex_session_record(agent_session: dict) -> bool:
    if (
        agent_session.get("agent") != CODEX_AGENT_NAME
        or agent_session.get("source") != CODEX_REPORT_SOURCE
        or agent_session.get("kind") != "id"
    ):
        return False
    return True


def codex_session_identifier(agent_information: dict) -> str | None:
    agent_session = agent_information.get("agent_session")
    if not isinstance(agent_session, dict):
        return None
    if not _is_codex_session_record(agent_session):
        return None
    session_identifier = agent_session.get("value")
    return session_identifier if isinstance(session_identifier, str) else None


def _rollout_contains_session(rollout_path, session_identifier):
    try:
        with rollout_path.open(encoding="utf-8") as rollout_file:
            first_record = json.loads(rollout_file.readline())
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(first_record, dict):
        return False
    if first_record.get("type") != SESSION_META_RECORD_TYPE:
        return False
    payload = first_record.get("payload")
    return isinstance(payload, dict) and payload.get("id") == session_identifier


def rollout_persists_session(sessions_directory: Path, session_identifier: str) -> bool:
    if not sessions_directory.is_dir():
        return False
    expected_filename_suffix = f"-{session_identifier}.jsonl"
    for rollout_path in sessions_directory.rglob("rollout-*.jsonl"):
        if not rollout_path.name.endswith(expected_filename_suffix):
            continue
        if _rollout_contains_session(rollout_path, session_identifier):
            return True
    return False


def fail(message: str) -> int:
    print(f"Codex session restart refused: {message}", file=sys.stderr)
    return 1


def _agent_information_from_stdin():
    try:
        agent_get_response = json.load(sys.stdin)
    except json.JSONDecodeError:
        return None
    if not isinstance(agent_get_response, dict):
        return None
    return agent_information_from_response(agent_get_response)


def _validate_inherited_session(session_identifier):
    inherited_session_identifier = os.environ.get("CODEX_THREAD_ID", "").strip()
    if (
        inherited_session_identifier
        and inherited_session_identifier != session_identifier
    ):
        return fail(
            f"Herdr targets {session_identifier}, but the running Codex session is "
            f"{inherited_session_identifier}."
        )
    return None


def _validate_saved_rollout(session_identifier):
    codex_home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    if not rollout_persists_session(codex_home / "sessions", session_identifier):
        return fail(
            f"session {session_identifier} has no saved rollout; the running process "
            "was left untouched."
        )
    return 0


def _preflight_codex_session(agent_information):
    if agent_information.get("agent") != CODEX_AGENT_NAME:
        return 0
    session_identifier = codex_session_identifier(agent_information)
    if not session_identifier:
        return fail("Herdr has no resumable Codex session for this pane.")
    failure = _validate_inherited_session(session_identifier)
    if failure is not None:
        return failure
    return _validate_saved_rollout(session_identifier)


def main() -> int:
    agent_information = _agent_information_from_stdin()
    if agent_information is None:
        return fail("Herdr returned an unreadable session target.")
    return _preflight_codex_session(agent_information)


if __name__ == "__main__":
    raise SystemExit(main())
