from __future__ import annotations

import json
import os
import subprocess

from catalog import select_servant_for_session
from interactive_session_detection import is_clawde_background_agent_session

from .peer_transport import PeerRequestFailure

PANE_REQUEST_TIMEOUT_SECONDS = 1.0


def session_identifier_from_pane_response(response_text: str) -> str | None:
    try:
        session = json.loads(response_text)["result"]["pane"]["agent_session"]
        if session.get("kind") != "id":
            return None
        session_identifier = session.get("value")
        return (
            session_identifier
            if isinstance(session_identifier, str) and session_identifier
            else None
        )
    except (ValueError, KeyError, TypeError, AttributeError):
        return None


def read_sending_session_identifier(pane_identifier: str) -> str | None:
    try:
        response = subprocess.run(
            ["herdr", "pane", "get", pane_identifier],
            capture_output=True,
            text=True,
            check=False,
            timeout=PANE_REQUEST_TIMEOUT_SECONDS,
        )
        if response.returncode != 0:
            return None
        return session_identifier_from_pane_response(response.stdout)
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return None


def sending_session_identifier(pane_identifier: str | None) -> str | None:
    session_identifier = os.environ.get("CODEX_THREAD_ID")
    if session_identifier:
        return session_identifier
    if not pane_identifier:
        return None
    return read_sending_session_identifier(pane_identifier)


def interactive_sender_name(pane_identifier: str | None) -> str | None:
    if os.environ.get("OPENCLAW_GATEWAY_PORT") or is_clawde_background_agent_session():
        return None
    session_identifier = sending_session_identifier(pane_identifier)
    if not session_identifier:
        return None
    return select_servant_for_session(session_identifier)["name"]


def directory_sender_name(
    agent_directory: dict, pane_identifier: str | None
) -> str | None:
    if not pane_identifier:
        return None
    for agent in agent_directory.values():
        if agent.get("paneId") == pane_identifier and agent.get("name"):
            return agent["name"]
    return None


def resolve_sender_name(agent_directory: dict) -> str:
    background_agent_name = os.environ.get("CLAWDE_AGENT_NAME")
    if background_agent_name:
        return background_agent_name
    pane_identifier = os.environ.get("HERDR_PANE_ID")
    sender_name = interactive_sender_name(pane_identifier) or directory_sender_name(
        agent_directory, pane_identifier
    )
    if not sender_name:
        raise PeerRequestFailure(
            "cannot identify the sender; use --sender with your current Servant "
            "or harness session name"
        )
    return sender_name


def validated_sender_name(sender_name: str) -> str:
    normalized_name = sender_name.strip()
    if not normalized_name or "\r" in normalized_name or "\n" in normalized_name:
        raise PeerRequestFailure("sender must be a nonempty, single-line name")
    return normalized_name


def signed_input_text(
    input_text: str, sender_name: str | None, agent_directory: dict
) -> str:
    if not input_text.strip():
        raise PeerRequestFailure("task text must not be empty")
    if sender_name is None:
        sender_name = resolve_sender_name(agent_directory)
    signature = f" — {validated_sender_name(sender_name)}"
    return (
        input_text
        if input_text.rstrip().endswith(signature)
        else f"{input_text}{signature}"
    )
