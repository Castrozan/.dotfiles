import pytest

import publish_current_usage_snapshot_to_ingest as publisher_entrypoint
from ingestion_snapshot_publisher import IngestionRefusedError

USAGE_SNAPSHOT = {
    "stats_last_computed_date": "2026-07-25",
    "account_label": "account-a1b2c3",
    "machine_label": "kira",
    "model_usage_totals": {
        "claude-opus-5": {
            "input_tokens": 1200,
            "output_tokens": 340,
            "cache_read_input_tokens": 98000,
            "cache_creation_input_tokens": 4500,
            "cost_usd": 1.25,
        }
    },
    "daily_activity": [
        {"message_count": 12, "session_count": 2, "tool_call_count": 40},
        {"message_count": 0, "session_count": 0, "tool_call_count": 0},
    ],
}

PUBLISH_ENVIRONMENT = {
    "INGEST_BASE_URL": "https://example.invalid/ingest",
    "INGEST_PRODUCER_SECRET": "seeded-by-the-owner",
}


class TestTheCurrentSnapshotIsPublishedUnderTheClaudeUsageContract:
    def test_publishes_the_contracted_payload_built_from_the_live_snapshot(
        self, monkeypatch
    ):
        published = {}

        def record_published_snapshot(
            topic, schema_version, payload, producer_label, environment
        ):
            published["topic"] = topic
            published["schemaVersion"] = schema_version
            published["payload"] = payload
            published["producer"] = producer_label
            return {"accepted": True}

        monkeypatch.setattr(
            publisher_entrypoint, "build_current_usage_snapshot", lambda: USAGE_SNAPSHOT
        )
        monkeypatch.setattr(
            publisher_entrypoint, "publish_snapshot", record_published_snapshot
        )

        acknowledgement = publisher_entrypoint.publish_current_usage_snapshot(
            PUBLISH_ENVIRONMENT
        )

        assert acknowledgement == {"accepted": True}
        assert published["topic"] == "claude-usage"
        assert published["schemaVersion"] == 1
        assert published["payload"]["accountLabel"] == "account-a1b2c3"
        assert published["payload"]["machineLabel"] == "kira"
        assert published["payload"]["totalCostUsd"] == 1.25
        assert published["payload"]["activity"]["activeDayCount"] == 1
        assert published["payload"]["models"][0]["model"] == "claude-opus-5"

    def test_publishes_nothing_when_the_machine_has_no_usage_to_report(
        self, monkeypatch
    ):
        monkeypatch.setattr(
            publisher_entrypoint, "build_current_usage_snapshot", lambda: None
        )
        monkeypatch.setattr(
            publisher_entrypoint,
            "publish_snapshot",
            lambda *unused: pytest.fail("nothing may be published without a snapshot"),
        )

        assert (
            publisher_entrypoint.publish_current_usage_snapshot(PUBLISH_ENVIRONMENT)
            is None
        )

    def test_refuses_to_publish_when_the_owner_has_not_seeded_the_ingest_mount(
        self, monkeypatch
    ):
        monkeypatch.setattr(
            publisher_entrypoint, "build_current_usage_snapshot", lambda: USAGE_SNAPSHOT
        )

        with pytest.raises(IngestionRefusedError):
            publisher_entrypoint.publish_current_usage_snapshot({})

    def test_reports_a_refusal_as_a_failing_exit_code(self, monkeypatch):
        monkeypatch.setattr(
            publisher_entrypoint, "build_current_usage_snapshot", lambda: USAGE_SNAPSHOT
        )
        monkeypatch.setattr(publisher_entrypoint.os, "environ", {})

        assert publisher_entrypoint.main() == 1

    def test_reports_an_absent_snapshot_as_a_successful_no_op(self, monkeypatch):
        monkeypatch.setattr(
            publisher_entrypoint, "build_current_usage_snapshot", lambda: None
        )

        assert publisher_entrypoint.main() == 0
