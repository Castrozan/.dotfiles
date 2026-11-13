from datetime import UTC, datetime

import pytest

import current_usage_snapshot
from ccusage_daily_reader import CcusageCollectionError

CACHE = {
    "firstSessionDate": "2026-05-26T16:44:20.085Z",
    "lastComputedDate": "2026-06-17",
    "dailyActivity": [
        {
            "date": "2026-06-17",
            "messageCount": 42,
            "sessionCount": 5,
            "toolCallCount": 130,
        }
    ],
}
OTEL_SUMMARY = {"session_count": 3}
CCUSAGE_SUMMARY = {
    "model_usage_totals": {
        "claude-opus-4-8": {
            "input_tokens": 11,
            "output_tokens": 22,
            "cache_read_input_tokens": 33,
            "cache_creation_input_tokens": 44,
            "cost_usd": 1.75,
        }
    },
    "daily_model_tokens": [
        {"date": "2026-11-11", "tokens_by_model": {"claude-opus-4-8": 110}}
    ],
    "stats_last_computed_date": "2026-11-11",
    "model_usage_first_date": "2026-11-10",
    "model_usage_source": "ccusage-offline",
}


class FixedSnapshotClock:
    @staticmethod
    def now(_timezone):
        return datetime(2026, 11, 13, 3, 0, tzinfo=UTC)


@pytest.fixture
def machine(monkeypatch):
    monkeypatch.setattr(
        current_usage_snapshot, "datetime", FixedSnapshotClock, raising=False
    )
    monkeypatch.setattr(
        current_usage_snapshot, "read_current_account_uuid", lambda path: "uuid"
    )
    monkeypatch.setattr(
        current_usage_snapshot, "derive_account_label", lambda uuid: "acct"
    )
    monkeypatch.setattr(
        current_usage_snapshot, "derive_machine_label", lambda host: "mach"
    )
    monkeypatch.setattr(current_usage_snapshot.socket, "gethostname", lambda: "chise")
    monkeypatch.setattr(current_usage_snapshot, "read_stats_cache", lambda path: CACHE)
    monkeypatch.setattr(
        current_usage_snapshot, "summarize_otel_metrics_file", lambda path: OTEL_SUMMARY
    )
    monkeypatch.setattr(
        current_usage_snapshot, "read_ccusage_daily_summary", lambda: CCUSAGE_SUMMARY
    )


def test_absent_account_returns_none_without_running_ccusage(machine, monkeypatch):
    monkeypatch.setattr(
        current_usage_snapshot, "read_current_account_uuid", lambda path: None
    )

    def must_not_run():
        raise AssertionError("ccusage must not run without an account")

    monkeypatch.setattr(
        current_usage_snapshot, "read_ccusage_daily_summary", must_not_run
    )
    assert current_usage_snapshot.build_current_usage_snapshot() is None


def test_collection_error_propagates_without_stale_model_fallback(machine, monkeypatch):
    def failing_collection():
        raise CcusageCollectionError("ccusage executable could not be started")

    monkeypatch.setattr(
        current_usage_snapshot, "read_ccusage_daily_summary", failing_collection
    )
    with pytest.raises(CcusageCollectionError, match="could not be started"):
        current_usage_snapshot.build_current_usage_snapshot()


def test_absent_ccusage_usage_returns_none(machine, monkeypatch):
    monkeypatch.setattr(
        current_usage_snapshot, "read_ccusage_daily_summary", lambda: None
    )
    assert current_usage_snapshot.build_current_usage_snapshot() is None


def test_snapshot_joins_current_model_data_with_historical_activity(machine):
    assert current_usage_snapshot.build_current_usage_snapshot() == {
        "schema_version": 1,
        "account_label": "acct",
        "machine_label": "mach",
        "captured_at_utc": "2026-11-13T03:00:00.000Z",
        "stats_first_session_date": "2026-05-26",
        "activity_last_computed_date": "2026-06-17",
        "daily_activity": [
            {
                "date": "2026-06-17",
                "message_count": 42,
                "session_count": 5,
                "tool_call_count": 130,
            }
        ],
        **CCUSAGE_SUMMARY,
        "otel_metrics": OTEL_SUMMARY,
    }
