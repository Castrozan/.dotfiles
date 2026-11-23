from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass

from ..document_fields import InvalidPeerDocument, current_timestamp
from .template import rendered_heartbeat

ATTENTION_STATES = frozenset({"blocked", "done"})
HANDED_OVER_STATE = "handed-over"


def heartbeat_name(requester: str) -> str:
    ascii_name = (
        unicodedata.normalize("NFKD", requester).encode("ascii", "ignore").decode()
    )
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", ascii_name).strip("-.")
    if not name:
        raise InvalidPeerDocument(f"{requester!r} cannot name a heartbeat")
    return name


@dataclass(frozen=True)
class HeartbeatAuthor:
    name: str
    requester: str
    requester_pane: str | None
    requester_host: str | None
    orchestrator: str


def published_heartbeat(
    heartbeat: dict, author: HeartbeatAuthor, previous_state: str | None
) -> dict:
    return {
        **asdict(author),
        "updated_at": current_timestamp(),
        "previous_state": previous_state,
        **heartbeat,
    }


def handed_over_heartbeat(record: dict) -> dict:
    return {
        **record,
        "state": HANDED_OVER_STATE,
        "previous_state": record["state"],
        "updated_at": current_timestamp(),
    }


def taken_back_heartbeat(record: dict) -> dict:
    return {
        **record,
        "state": record["previous_state"],
        "previous_state": HANDED_OVER_STATE,
        "updated_at": current_timestamp(),
    }


def needs_orchestrator_attention(record: dict) -> bool:
    return (
        record["state"] in ATTENTION_STATES
        and record["state"] != record["previous_state"]
    )


def rendered_record(record: dict) -> str:
    published = f"Published {record['updated_at']} by {record['requester']}"
    return f"{published}\n\n{rendered_heartbeat(record)}"


def notification_text(record: dict) -> str:
    return (
        f"{record['requester']} is {record['state']}: {record['next']} "
        f"Read it: orchestrator heartbeat show {record['name']}"
    )
