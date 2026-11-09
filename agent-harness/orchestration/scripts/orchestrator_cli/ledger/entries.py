from __future__ import annotations

import secrets
from datetime import datetime, timezone

from ..document_fields import InvalidPeerDocument, current_timestamp

ASK_KIND = "ask"
FACT_KIND = "fact"
OPEN_STATE = "open"
DONE_STATE = "done"
STANDING_STATE = "standing"
ORCHESTRATOR_OWNER = "orchestrator"


def new_entry_identifier() -> str:
    return f"L-{datetime.now(timezone.utc):%Y%m%d}-{secrets.token_hex(3)}"


def new_entry(kind: str, words: str, owner: str | None, orchestrator: str) -> dict:
    if not words.strip():
        raise InvalidPeerDocument("--words must carry Lucas's words verbatim")
    return {
        "id": new_entry_identifier(),
        "kind": kind,
        "words": words.strip(),
        "owner": owner or ORCHESTRATOR_OWNER,
        "orchestrator": orchestrator,
        "state": OPEN_STATE if kind == ASK_KIND else STANDING_STATE,
        "recorded_at": current_timestamp(),
    }


def closed_entry(entry: dict, evidence: str) -> dict:
    if entry["kind"] != ASK_KIND or entry["state"] != OPEN_STATE:
        raise InvalidPeerDocument(f"{entry['id']} is not an open ask")
    if not evidence.strip():
        raise InvalidPeerDocument("--evidence must name what proves the ask done")
    return {
        **entry,
        "state": DONE_STATE,
        "evidence": evidence.strip(),
        "closed_at": current_timestamp(),
    }


def entries_of(entries: list[dict], orchestrator: str) -> list[dict]:
    owned = [entry for entry in entries if entry["orchestrator"] == orchestrator]
    return sorted(owned, key=lambda entry: entry["recorded_at"])


def open_asks(entries: list[dict], orchestrator: str) -> list[dict]:
    return [
        entry
        for entry in entries_of(entries, orchestrator)
        if entry["kind"] == ASK_KIND and entry["state"] == OPEN_STATE
    ]
