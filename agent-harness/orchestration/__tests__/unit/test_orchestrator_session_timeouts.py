from datetime import datetime, timedelta, timezone

from hypothesis import given
from hypothesis import strategies as st
from orchestrator_cli.watch.session_timeouts import (
    SessionRecords,
    WatchedSession,
    is_finished,
    session_deadline,
    session_records,
)

BEGINNING = datetime(2026, 11, 8, 9, 0, tzinfo=timezone.utc)
TIMEOUT = timedelta(minutes=15)
NO_RECORDS = SessionRecords({}, {})

optional_offsets = st.one_of(st.none(), st.integers(min_value=0, max_value=10_000))


def moment(offset_minutes):
    if offset_minutes is None:
        return None
    return BEGINNING + timedelta(minutes=offset_minutes)


@given(
    first_seen=st.integers(min_value=0, max_value=10_000),
    heard=optional_offsets,
    answered=optional_offsets,
    reminded=optional_offsets,
)
def test_a_session_is_due_one_timeout_after_the_latest_thing_heard_or_reminded(
    first_seen, heard, answered, reminded
):
    session = WatchedSession(
        "wW:p1", "idle", moment(first_seen), moment(heard), moment(reminded)
    )
    answers = {} if answered is None else {"wW:p1": moment(answered)}
    spoken = [offset for offset in (heard, answered) if offset is not None]
    last_heard = max(spoken) if spoken else first_seen
    expected_anchor = last_heard if reminded is None else max(last_heard, reminded)
    assert (
        session_deadline(session, SessionRecords(answers, {}), TIMEOUT)
        == moment(expected_anchor) + TIMEOUT
    )


@given(status=st.sampled_from(["idle", "blocked", "done", "unknown", "working"]))
def test_only_a_done_report_on_a_pane_no_longer_working_finishes_a_session(status):
    session = WatchedSession("wW:p1", status, BEGINNING)
    finished = SessionRecords({}, {"wW:p1": "done"})
    assert is_finished(session, finished) == (status != "working")
    assert not is_finished(session, SessionRecords({}, {"wW:p1": "working"}))
    assert not is_finished(session, NO_RECORDS)


def test_records_give_each_pane_its_latest_answer_and_latest_report_state():
    reports = [
        {
            "requester_pane": "wW:p1",
            "state": "done",
            "updated_at": "2026-11-08T09:10:00+00:00",
        },
        {
            "requester_pane": "wW:p1",
            "state": "working",
            "updated_at": "2026-11-08T09:05:00+00:00",
        },
    ]
    cards = [
        {
            "requester_pane": "wW:p1",
            "created_at": "2026-11-08T09:00:00+00:00",
            "answer": {"decided_at": "2026-11-08T09:20:00+00:00"},
        },
        {"requester_pane": None, "created_at": "2026-11-08T09:30:00+00:00"},
    ]
    records = session_records(reports, cards)
    assert records.answered_at == {"wW:p1": BEGINNING + timedelta(minutes=20)}
    assert records.report_states == {"wW:p1": "done"}
