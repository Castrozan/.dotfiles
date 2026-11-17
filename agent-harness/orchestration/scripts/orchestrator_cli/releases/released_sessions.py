from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from ..document_fields import current_timestamp
from ..peer_messenger import PeerMessageFailure, peer_pane
from ..record_store import all_records, state_directory
from ..watch.herdr_events import live_pane

FILING_REFUSAL = (
    "{orchestrator} released this session to Lucas on {released_at}: he drives it "
    "directly, so nothing was filed and {orchestrator} was not told. Tell Lucas in "
    "your pane instead; this replaces your brief's Contract."
)
MESSAGE_REFUSAL = (
    "{orchestrator} released {session} to Lucas on {released_at}, and it is his to "
    "drive until he hands it back; nothing was sent. Once he does, run "
    "`orchestrator handover {pane} --take-back`."
)


class SessionReleased(Exception):
    pass


@dataclass(frozen=True)
class SessionIdentity:
    panes: frozenset[str]
    session_identifier: str | None = None


def release_directory() -> Path:
    return state_directory("orchestrator-releases")


def harness_session_identifier(pane: dict) -> str | None:
    agent_session = pane.get("agent_session")
    if isinstance(agent_session, dict) and agent_session.get("kind") == "id":
        return agent_session.get("value") or None
    return None


def identity_of_pane(pane_id: str) -> SessionIdentity:
    pane = live_pane(pane_id)
    if pane is None:
        return SessionIdentity(frozenset({pane_id}))
    return SessionIdentity(
        frozenset({pane_id, pane.get("pane_id") or pane_id}),
        harness_session_identifier(pane),
    )


def identity_of_target(target: str) -> SessionIdentity:
    try:
        return identity_of_pane(peer_pane(target) or target)
    except PeerMessageFailure:
        return identity_of_pane(target)


def is_same_session(identity: SessionIdentity, release: dict) -> bool:
    return bool(identity.panes & set(release["panes"])) or (
        identity.session_identifier is not None
        and identity.session_identifier == release["session_identifier"]
    )


def releases_of(identity: SessionIdentity, releases: list[dict]) -> list[dict]:
    return [release for release in releases if is_same_session(identity, release)]


def new_release(
    pane_id: str, identity: SessionIdentity, session: str, orchestrator: str
) -> dict:
    return {
        "name": pane_id.replace(":", "-"),
        "pane": pane_id,
        "panes": sorted(identity.panes),
        "session_identifier": identity.session_identifier,
        "session": session,
        "orchestrator": orchestrator,
        "released_at": current_timestamp(),
    }


def released_panes() -> frozenset[str]:
    return frozenset(
        pane_id
        for release in all_records(release_directory())
        for pane_id in release["panes"]
    )


def releases_of_filer() -> list[dict]:
    releases = all_records(release_directory())
    pane_id = os.environ.get("HERDR_PANE_ID")
    if not releases or not pane_id:
        return []
    return releases_of(SessionIdentity(frozenset({pane_id})), releases) or releases_of(
        identity_of_pane(pane_id), releases
    )


def require_unreleased_filer() -> None:
    releases = releases_of_filer()
    if releases:
        raise SessionReleased(FILING_REFUSAL.format(**releases[0]))


def require_unreleased_target(target: str) -> None:
    releases = all_records(release_directory())
    if not releases:
        return
    matching = releases_of(identity_of_target(target), releases)
    if matching:
        raise SessionReleased(MESSAGE_REFUSAL.format(**matching[0]))
