from __future__ import annotations

import json
import os
import subprocess

from catalog import select_servant_for_session
from interactive_session_detection import is_clawde_background_agent_session

from .peer_transport import PeerRequestFailure

PANE_REQUEST_TIMEOUT_SECONDS = 1.0


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
        return _reported_session_identifier(response.stdout)
    except (
        OSError,
        subprocess.TimeoutExpired,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
    ):
        return None


def _reported_session_identifier(response_text: str) -> str | None:
    session = json.loads(response_text)["result"]["pane"]["agent_session"]
    if session.get("kind") != "id":
        return None
    session_identifier = session.get("value")
    if isinstance(session_identifier, str) and session_identifier:
        return session_identifier
    return None


def resolve_sender_name(agent_directory: dict) -> str:
    background_agent_name = os.environ.get("CLAWDE_AGENT_NAME")
    if background_agent_name:
        return background_agent_name
    pane_identifier = os.environ.get("HERDR_PANE_ID")
    session_identifier = _servant_session_identifier(pane_identifier)
    if session_identifier:
        return select_servant_for_session(session_identifier)["name"]
    pane_agent_name = _sending_pane_agent_name(pane_identifier, agent_directory)
    if pane_agent_name:
        return pane_agent_name
    raise PeerRequestFailure(
        "cannot identify the sender; use --sender with your current Servant "
        "or harness session name"
    )


def _servant_session_identifier(pane_identifier: str | None) -> str | None:
    if os.environ.get("OPENCLAW_GATEWAY_PORT") or is_clawde_background_agent_session():
        return None
    session_identifier = os.environ.get("CODEX_THREAD_ID")
    if session_identifier:
        return session_identifier
    if pane_identifier:
        return read_sending_session_identifier(pane_identifier)
    return None


def _sending_pane_agent_name(
    pane_identifier: str | None, agent_directory: dict
) -> str | None:
    if not pane_identifier:
        return None
    for agent in agent_directory.values():
        if agent.get("paneId") == pane_identifier and agent.get("name"):
            return agent["name"]
    return None


def signed_input_text(
    input_text: str, sender_name: str | None, agent_directory: dict
) -> str:
    if not input_text.strip():
        raise PeerRequestFailure("task text must not be empty")
    resolved_sender_name = _validated_sender_name(sender_name, agent_directory)
    signature = f" — {resolved_sender_name}"
    return (
        input_text
        if input_text.rstrip().endswith(signature)
        else f"{input_text}{signature}"
    )


def _validated_sender_name(sender_name: str | None, agent_directory: dict) -> str:
    resolved_sender_name = (
        resolve_sender_name(agent_directory) if sender_name is None else sender_name
    ).strip()
    if not resolved_sender_name or any(
        character in resolved_sender_name for character in "\r\n"
    ):
        raise PeerRequestFailure("sender must be a nonempty, single-line name")
    return resolved_sender_name
