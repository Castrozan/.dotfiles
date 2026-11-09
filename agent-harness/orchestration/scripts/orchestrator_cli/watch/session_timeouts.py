from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from ..decisions.cards import ESCALATED_STATE, OPEN_STATE

FINISHED_REPORT_STATE = "done"
BLOCKED_REPORT_STATE = "blocked"
HANDED_OVER_REPORT_STATE = "handed-over"
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
    report_states: dict[str, str]
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


def awaited_decisions(pane_id: str, report: dict, cards: list[dict]) -> set[str]:
    unresolved = {
        card["id"]
        for card in cards
        if card.get("requester_pane") == pane_id
        and card["state"] in (OPEN_STATE, ESCALATED_STATE)
    }
    return unresolved | set(report.get("open_decisions", []))


def waits_only_on_human(pane_id: str, report: dict, cards: list[dict]) -> bool:
    if report["state"] != BLOCKED_REPORT_STATE:
        return False
    card_states = {card["id"]: card["state"] for card in cards}
    awaited = awaited_decisions(pane_id, report, cards)
    return bool(awaited) and all(
        card_states.get(identifier) == ESCALATED_STATE for identifier in awaited
    )


def session_records(reports: list[dict], cards: list[dict]) -> SessionRecords:
    stamps = [
        (report.get("requester_pane"), report["updated_at"]) for report in reports
    ]
    stamps += [(card.get("requester_pane"), card_activity_time(card)) for card in cards]
    oldest_first = sorted(reports, key=lambda report: report["updated_at"])
    latest_reports = {
        report["requester_pane"]: report
        for report in oldest_first
        if report.get("requester_pane")
    }
    return SessionRecords(
        latest_answer_times(stamps),
        {pane_id: report["state"] for pane_id, report in latest_reports.items()},
        frozenset(
            pane_id
            for pane_id, report in latest_reports.items()
            if waits_only_on_human(pane_id, report, cards)
        ),
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
    report_state = records.report_states.get(session.pane_id)
    if report_state == HANDED_OVER_REPORT_STATE:
        return True
    return report_state == FINISHED_REPORT_STATE and session.status != WORKING_STATUS


def waits_on_human(session: WatchedSession, records: SessionRecords) -> bool:
    return session.pane_id in records.waiting_on_human


def timeout_line(
    session: WatchedSession, records: SessionRecords, now: datetime
) -> str:
    quiet_seconds = (now - last_heard_at(session, records)).total_seconds()
    report_state = records.report_states.get(session.pane_id, "none")
    return (
        f"TIMEOUT {session.pane_id} {session.status} "
        f"quiet-minutes={int(quiet_seconds // 60)} report={report_state}"
    )
