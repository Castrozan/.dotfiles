from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from ..decisions.cards import ESCALATED_STATE, OPEN_STATE

FINISHED_HEARTBEAT_STATE = "done"
BLOCKED_HEARTBEAT_STATE = "blocked"
HANDED_OVER_HEARTBEAT_STATE = "handed-over"
WORKING_STATUS = "working"


@dataclass
class WatchedSession:
    pane_id: str
    status: str
    first_seen_at: datetime
    heard_at: datetime | None = None
    reminded_at: datetime | None = None


@dataclass(frozen=True)
class SessionRecords:
    answered_at: dict[str, datetime]
    heartbeat_states: dict[str, str]
    waiting_on_human: frozenset[str] = frozenset()


def current_time() -> datetime:
    return datetime.now(timezone.utc)


def card_activity_time(card: dict) -> str:
    return card.get("answer", {}).get("decided_at", card["created_at"])


def latest_answer_times(stamps: list[tuple[str | None, str]]) -> dict[str, datetime]:
    answered_at: dict[str, datetime] = {}
    for pane_id, stamp in stamps:
        if pane_id:
            answer_time = datetime.fromisoformat(stamp)
            answered_at[pane_id] = max(
                answer_time, answered_at.get(pane_id, answer_time)
            )
    return answered_at


def waits_only_on_human(
    heartbeat: dict, awaited: set[str], card_states: dict[str, str]
) -> bool:
    return (
        heartbeat["state"] == BLOCKED_HEARTBEAT_STATE
        and bool(awaited)
        and all(
            card_states.get(identifier) == ESCALATED_STATE for identifier in awaited
        )
    )


def panes_waiting_on_human(
    latest_heartbeats: dict[str, dict], cards: list[dict]
) -> frozenset[str]:
    card_states = {card["id"]: card["state"] for card in cards}
    unresolved: dict[str, set[str]] = defaultdict(set)
    for card in cards:
        if card["state"] in (OPEN_STATE, ESCALATED_STATE):
            unresolved[card.get("requester_pane")].add(card["id"])
    return frozenset(
        pane_id
        for pane_id, heartbeat in latest_heartbeats.items()
        if waits_only_on_human(
            heartbeat,
            unresolved[pane_id] | set(heartbeat.get("open_decisions", [])),
            card_states,
        )
    )


def session_records(heartbeats: list[dict], cards: list[dict]) -> SessionRecords:
    stamps = [
        (heartbeat.get("requester_pane"), heartbeat["updated_at"])
        for heartbeat in heartbeats
    ]
    stamps += [(card.get("requester_pane"), card_activity_time(card)) for card in cards]
    oldest_first = sorted(heartbeats, key=lambda heartbeat: heartbeat["updated_at"])
    latest_heartbeats = {
        heartbeat["requester_pane"]: heartbeat
        for heartbeat in oldest_first
        if heartbeat.get("requester_pane")
    }
    return SessionRecords(
        latest_answer_times(stamps),
        {
            pane_id: heartbeat["state"]
            for pane_id, heartbeat in latest_heartbeats.items()
        },
        panes_waiting_on_human(latest_heartbeats, cards),
    )


def last_heard_at(session: WatchedSession, records: SessionRecords) -> datetime:
    heard = (session.heard_at, records.answered_at.get(session.pane_id))
    return max(filter(None, heard), default=session.first_seen_at)


def session_deadline(
    session: WatchedSession, records: SessionRecords, timeout: timedelta
) -> datetime:
    last_heard = last_heard_at(session, records)
    return max(session.reminded_at or last_heard, last_heard) + timeout


def is_finished(session: WatchedSession, records: SessionRecords) -> bool:
    heartbeat_state = records.heartbeat_states.get(session.pane_id)
    if heartbeat_state == HANDED_OVER_HEARTBEAT_STATE:
        return True
    return (
        heartbeat_state == FINISHED_HEARTBEAT_STATE and session.status != WORKING_STATUS
    )


def waits_on_human(session: WatchedSession, records: SessionRecords) -> bool:
    return session.pane_id in records.waiting_on_human


def timeout_line(
    session: WatchedSession, records: SessionRecords, now: datetime
) -> str:
    quiet_seconds = (now - last_heard_at(session, records)).total_seconds()
    heartbeat_state = records.heartbeat_states.get(session.pane_id, "none")
    return (
        f"TIMEOUT {session.pane_id} {session.status} "
        f"quiet-minutes={int(quiet_seconds // 60)} heartbeat={heartbeat_state}"
    )
