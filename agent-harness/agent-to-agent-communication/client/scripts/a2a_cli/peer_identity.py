from __future__ import annotations

import json
import subprocess

from catalog import select_servant_for_session
from interactive_session_detection import is_inside_a_clawde_agent_workspace

PANE_LIST_TIMEOUT_SECONDS = 2.0
HARNESSES_REPORTING_SESSION_IDENTIFIERS = frozenset({"claude", "codex", "opencode"})


def reports_a_harness_session(agent_session: object) -> bool:
    return (
        isinstance(agent_session, dict)
        and agent_session.get("kind") == "id"
        and agent_session.get("agent") in HARNESSES_REPORTING_SESSION_IDENTIFIERS
    )


def harness_session_identifier(agent_session: object) -> str | None:
    if not reports_a_harness_session(agent_session):
        return None
    session_identifier = agent_session.get("value")
    if isinstance(session_identifier, str) and session_identifier:
        return session_identifier
    return None


def read_live_panes() -> list[dict]:
    try:
        response = subprocess.run(
            ["herdr", "pane", "list"],
            capture_output=True,
            text=True,
            check=False,
            timeout=PANE_LIST_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if response.returncode != 0:
        return []
    try:
        panes = json.loads(response.stdout)["result"]["panes"]
    except (ValueError, KeyError, TypeError):
        return []
    return (
        [pane for pane in panes if isinstance(pane, dict)]
        if isinstance(panes, list)
        else []
    )


def identity_of_pane(pane: dict) -> dict:
    session_identifier = harness_session_identifier(pane.get("agent_session"))
    if not session_identifier:
        return {}
    identity = {"sessionId": session_identifier}
    if not is_inside_a_clawde_agent_workspace(pane.get("cwd") or ""):
        identity["servant"] = select_servant_for_session(session_identifier)["name"]
    return identity


def with_peer_identities(agent_directory: dict) -> dict:
    identity_by_pane_identifier = {
        pane.get("pane_id"): identity_of_pane(pane) for pane in read_live_panes()
    }
    return {
        name: {**entry, **identity_by_pane_identifier.get(entry.get("paneId"), {})}
        for name, entry in agent_directory.items()
    }
