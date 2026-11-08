from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

FINISHED_REPORT_STATE = "done"
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


def session_records(reports: list[dict], cards: list[dict]) -> SessionRecords:
    stamps = [
        (report.get("requester_pane"), report["updated_at"]) for report in reports
    ]
    stamps += [(card.get("requester_pane"), card_activity_time(card)) for card in cards]
    oldest_first = sorted(reports, key=lambda report: report["updated_at"])
    report_states = {
        report["requester_pane"]: report["state"]
        for report in oldest_first
        if report.get("requester_pane")
    }
    return SessionRecords(latest_answer_times(stamps), report_states)


def last_heard_at(session: WatchedSession, records: SessionRecords) -> datetime:
    heard = (session.heard_at, records.answered_at.get(session.pane_id))
    return max(filter(None, heard), default=session.first_seen_at)


def session_deadline(
    session: WatchedSession, records: SessionRecords, timeout: timedelta
) -> datetime:
    last_heard = last_heard_at(session, records)
    return max(session.reminded_at or last_heard, last_heard) + timeout


def is_finished(session: WatchedSession, records: SessionRecords) -> bool:
    return (
        records.report_states.get(session.pane_id) == FINISHED_REPORT_STATE
        and session.status != WORKING_STATUS
    )


def timeout_line(
    session: WatchedSession, records: SessionRecords, now: datetime
) -> str:
    quiet_seconds = (now - last_heard_at(session, records)).total_seconds()
    report_state = records.report_states.get(session.pane_id, "none")
    return (
        f"TIMEOUT {session.pane_id} {session.status} "
        f"quiet-minutes={int(quiet_seconds // 60)} report={report_state}"
    )
