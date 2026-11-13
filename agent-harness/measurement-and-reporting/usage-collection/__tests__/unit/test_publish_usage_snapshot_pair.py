import json

import pytest

import publish_current_usage_snapshot_to_ingest as publisher_entrypoint
from ingestion_snapshot_publisher import IngestionRefusedError

USAGE_SNAPSHOT = {
    "schema_version": 1,
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
        {
            "date": "2026-07-24",
            "message_count": 12,
            "session_count": 2,
            "tool_call_count": 40,
        }
    ],
}
EXPECTED_RAW_BODY = (
    json.dumps(USAGE_SNAPSHOT, indent=2, sort_keys=True) + "\n"
).encode("utf-8")
EXPECTED_OBJECT_KEY = "snapshots/account-a1b2c3-kira.json"
PUBLISH_ENVIRONMENT = {
    "INGEST_BASE_URL": "https://example.invalid/ingest",
    "INGEST_PRODUCER_SECRET": "seeded-by-the-owner",
}


class PublicationRecorder:
    def __init__(self, monkeypatch, snapshot_outcome=None, artifact_outcome=None):
        self.calls = []
        self.collection_count = 0
        self.snapshot_outcome = snapshot_outcome or (lambda: {"accepted": True})
        self.artifact_outcome = artifact_outcome or (
            lambda: {
                "objectKey": EXPECTED_OBJECT_KEY,
                "byteLength": len(EXPECTED_RAW_BODY),
            }
        )

        def collect_once():
            self.collection_count += 1
            return USAGE_SNAPSHOT

        def record_snapshot(
            topic, schema_version, payload, producer_label, environment
        ):
            self.calls.append(("snapshot", topic, schema_version, payload))
            return self.snapshot_outcome()

        def record_artifact(object_key, content_type, body_bytes, environment):
            self.calls.append(("artifact", object_key, content_type, body_bytes))
            return self.artifact_outcome()

        monkeypatch.setattr(
            publisher_entrypoint, "build_current_usage_snapshot", collect_once
        )
        monkeypatch.setattr(publisher_entrypoint, "publish_snapshot", record_snapshot)
        monkeypatch.setattr(publisher_entrypoint, "publish_artifact", record_artifact)


def refuse():
    raise IngestionRefusedError("the ingest api refused the artifact with status 500")


class TestTheSnapshotIsCollectedOnceAndSentAsNormalizedThenRaw:
    def test_collects_the_usage_once_and_prepares_both_bodies_from_that_collection(
        self, monkeypatch
    ):
        recorder = PublicationRecorder(monkeypatch)

        publisher_entrypoint.publish_current_usage_snapshot(PUBLISH_ENVIRONMENT)

        assert recorder.collection_count == 1

    def test_sends_the_normalized_event_before_the_raw_artifact(self, monkeypatch):
        recorder = PublicationRecorder(monkeypatch)

        publisher_entrypoint.publish_current_usage_snapshot(PUBLISH_ENVIRONMENT)

        assert [call[0] for call in recorder.calls] == ["snapshot", "artifact"]
        assert recorder.calls[0][1:3] == ("claude-usage", 1)

    def test_sends_the_exact_raw_utf8_json_under_the_snapshots_key(self, monkeypatch):
        recorder = PublicationRecorder(monkeypatch)

        publisher_entrypoint.publish_current_usage_snapshot(PUBLISH_ENVIRONMENT)

        _, object_key, content_type, body_bytes = recorder.calls[1]
        assert object_key == EXPECTED_OBJECT_KEY
        assert content_type == "application/json"
        assert body_bytes == EXPECTED_RAW_BODY

    def test_returns_both_acknowledgements_under_their_own_names(self, monkeypatch):
        PublicationRecorder(monkeypatch)

        acknowledgement = publisher_entrypoint.publish_current_usage_snapshot(
            PUBLISH_ENVIRONMENT
        )

        assert acknowledgement == {
            "snapshot": {"accepted": True},
            "artifact": {
                "objectKey": EXPECTED_OBJECT_KEY,
                "byteLength": len(EXPECTED_RAW_BODY),
            },
        }


class TestAPartialPairIsNeverReportedAsSuccess:
    def test_refuses_when_the_raw_artifact_is_refused_after_the_event_was_accepted(
        self, monkeypatch
    ):
        PublicationRecorder(monkeypatch, artifact_outcome=refuse)

        with pytest.raises(IngestionRefusedError, match="status 500"):
            publisher_entrypoint.publish_current_usage_snapshot(PUBLISH_ENVIRONMENT)

    def test_reports_the_partial_pair_as_a_failing_exit_code(self, monkeypatch, capsys):
        PublicationRecorder(monkeypatch, artifact_outcome=refuse)
        monkeypatch.setattr(publisher_entrypoint.os, "environ", PUBLISH_ENVIRONMENT)

        assert publisher_entrypoint.main() == 1
        assert "status 500" in capsys.readouterr().err

    def test_never_sends_the_artifact_when_the_normalized_event_is_refused(
        self, monkeypatch
    ):
        recorder = PublicationRecorder(monkeypatch, snapshot_outcome=refuse)

        with pytest.raises(IngestionRefusedError):
            publisher_entrypoint.publish_current_usage_snapshot(PUBLISH_ENVIRONMENT)

        assert [call[0] for call in recorder.calls] == ["snapshot"]


class TestNothingIsSentWhenTheActivityWasNotMeasured:
    def test_refuses_before_any_request_when_daily_activity_was_not_measured(
        self, monkeypatch
    ):
        recorder = PublicationRecorder(monkeypatch)
        unmeasured_snapshot = {
            key: value
            for key, value in USAGE_SNAPSHOT.items()
            if key != "daily_activity"
        }
        monkeypatch.setattr(
            publisher_entrypoint,
            "build_current_usage_snapshot",
            lambda: unmeasured_snapshot,
        )

        with pytest.raises(IngestionRefusedError, match="daily_activity"):
            publisher_entrypoint.publish_current_usage_snapshot(PUBLISH_ENVIRONMENT)

        assert recorder.calls == []

    def test_a_measured_empty_activity_list_is_published_as_zero_activity(
        self, monkeypatch
    ):
        recorder = PublicationRecorder(monkeypatch)
        empty_activity_snapshot = {**USAGE_SNAPSHOT, "daily_activity": []}
        monkeypatch.setattr(
            publisher_entrypoint,
            "build_current_usage_snapshot",
            lambda: empty_activity_snapshot,
        )

        publisher_entrypoint.publish_current_usage_snapshot(PUBLISH_ENVIRONMENT)

        assert recorder.calls[0][3]["activity"]["activeDayCount"] == 0
