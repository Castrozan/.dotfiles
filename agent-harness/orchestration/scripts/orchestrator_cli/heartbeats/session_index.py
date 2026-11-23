from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..document_fields import (
    InvalidPeerDocument,
    current_timestamp,
    nonempty_text,
    require_object,
    required_text_items,
)
from ..record_store import all_records, save_record, state_directory

REQUIRED_TEXT_FIELDS = ("name", "orchestrator", "goal", "heartbeat", "opened_at")
OPTIONAL_TEXT_FIELDS = ("host", "pane", "brief", "closed_at", "closed_because")


@dataclass(frozen=True)
class SessionPlacement:
    host: str | None
    pane: str | None
    peer_names: frozenset[str]

    def folded_names(self) -> set[str]:
        return {name.casefold() for name in self.peer_names if name}


def index_directory() -> Path:
    return state_directory("orchestrator-index")


def optional_text(document: dict, field: str) -> str | None:
    if document.get(field) is None:
        return None
    return nonempty_text(document, field)


def validated_entry(document) -> dict:
    document = require_object(document, "an index entry")
    entry = {field: nonempty_text(document, field) for field in REQUIRED_TEXT_FIELDS}
    entry |= {field: optional_text(document, field) for field in OPTIONAL_TEXT_FIELDS}
    entry["peer_names"] = required_text_items(document, "peer_names")
    if (entry["closed_at"] is None) != (entry["closed_because"] is None):
        raise InvalidPeerDocument("a closed index entry says when and why it closed")
    return entry


def new_entry(
    name: str,
    orchestrator: str,
    placement: SessionPlacement,
    goal: str,
    brief: str | None = None,
) -> dict:
    return {
        "name": name,
        "orchestrator": orchestrator,
        "host": placement.host,
        "pane": placement.pane,
        "peer_names": sorted(placement.folded_names()),
        "goal": goal,
        "brief": brief,
        "opened_at": current_timestamp(),
        "closed_at": None,
        "closed_because": None,
    }


def closed_entry(entry: dict, because: str) -> dict:
    return {**entry, "closed_at": current_timestamp(), "closed_because": because}


def reopened_entry(entry: dict) -> dict:
    return {**entry, "closed_at": None, "closed_because": None}


def is_open(entry: dict) -> bool:
    return entry["closed_at"] is None


def save_entry(entry: dict, heartbeat_path: Path) -> dict:
    entry = validated_entry({**entry, "heartbeat": str(heartbeat_path)})
    save_record(index_directory(), entry["name"], entry)
    return entry


def entries_of(orchestrator: str) -> list[dict]:
    return [
        validated_entry(record)
        for record in all_records(index_directory())
        if record.get("orchestrator") == orchestrator
    ]


def only_match(matches: list[dict], description: str) -> dict | None:
    if len(matches) > 1:
        names = ", ".join(sorted(entry["name"] for entry in matches))
        raise InvalidPeerDocument(f"{description} matches several sessions ({names})")
    return matches[0] if matches else None


def placed_alike(entry: dict, placement: SessionPlacement) -> bool:
    if not is_open(entry) or entry["host"] != placement.host:
        return False
    if placement.pane:
        return entry["pane"] == placement.pane
    return bool(placement.folded_names() & set(entry["peer_names"]))


def filer_entry(entries: list[dict], placement: SessionPlacement) -> dict | None:
    matches = [entry for entry in entries if placed_alike(entry, placement)]
    return only_match(matches, " ".join(sorted(placement.folded_names())))


def named_entry(entries: list[dict], session: str) -> dict:
    for matches in (
        [entry for entry in entries if entry["name"] == session],
        [entry for entry in entries if entry["pane"] == session],
        [entry for entry in entries if session.casefold() in entry["peer_names"]],
    ):
        entry = only_match(matches, session)
        if entry:
            return entry
    raise InvalidPeerDocument(f"no session in the index is called {session}")
