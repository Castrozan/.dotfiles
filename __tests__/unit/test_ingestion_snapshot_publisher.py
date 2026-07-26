import re

import pytest

from ingestion_snapshot_publisher import (
    IngestionRefusedError,
    build_ingestion_event,
    build_topic_endpoint_url,
    read_required_environment_value,
    resolve_event_source,
)

PAYLOAD = {"recordedAt": "2026-07-24T03:26:24.774576+00:00", "commit": "5667c9f6"}


class TestIngestionEnvelopeMatchesTheTopicContract:
    def test_stamps_the_topic_and_schema_version_the_api_serves(self):
        event = build_ingestion_event("dotfiles-test-baseline", 1, PAYLOAD, "ci", None)

        assert event["topic"] == "dotfiles-test-baseline"
        assert event["schemaVersion"] == 1
        assert event["producer"] == "ci"
        assert event["payload"] == PAYLOAD

    def test_produces_a_utc_timestamp_the_contract_pattern_accepts(self):
        event = build_ingestion_event("dotfiles-test-baseline", 1, PAYLOAD, "ci", None)

        assert re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z", event["producedAt"]
        )

    def test_omits_the_source_object_entirely_when_no_run_context_exists(self):
        event = build_ingestion_event("dotfiles-test-baseline", 1, PAYLOAD, "ci", None)

        assert "source" not in event

    def test_carries_the_run_context_when_the_producer_resolves_one(self):
        source = {"repository": "owner/dotfiles", "commit": "5667c9f6"}
        event = build_ingestion_event(
            "dotfiles-test-baseline", 1, PAYLOAD, "ci", source
        )

        assert event["source"] == source

    def test_emits_no_envelope_key_the_contract_does_not_declare(self):
        event = build_ingestion_event("dotfiles-test-baseline", 1, PAYLOAD, "ci", None)

        assert set(event) == {
            "topic",
            "schemaVersion",
            "producedAt",
            "producer",
            "payload",
        }


class TestRunContextIsResolvedFromTheCiEnvironment:
    def test_builds_the_repository_commit_and_run_url_from_the_workflow(self):
        source = resolve_event_source(
            {
                "GITHUB_REPOSITORY": "owner/dotfiles",
                "GITHUB_SHA": "5667c9f65667c9f65667c9f65667c9f65667c9f6",
                "GITHUB_SERVER_URL": "https://github.com",
                "GITHUB_RUN_ID": "42",
            }
        )

        assert source == {
            "repository": "owner/dotfiles",
            "commit": "5667c9f65667c9f65667c9f65667c9f65667c9f6",
            "runUrl": "https://github.com/owner/dotfiles/actions/runs/42",
        }

    def test_drops_the_run_url_rather_than_emitting_a_partial_one(self):
        source = resolve_event_source(
            {"GITHUB_REPOSITORY": "owner/dotfiles", "GITHUB_SHA": "5667c9f6"}
        )

        assert source == {"repository": "owner/dotfiles", "commit": "5667c9f6"}

    def test_resolves_to_nothing_outside_a_workflow_run(self):
        assert resolve_event_source({}) is None


class TestTopicRoutingAndEnvironmentRefusals:
    def test_mounts_every_topic_under_its_own_path_on_the_ingest_api(self):
        assert (
            build_topic_endpoint_url("https://ingest.example/ingest/", "a-topic")
            == "https://ingest.example/ingest/a-topic"
        )

    def test_refuses_to_publish_without_the_value_the_request_needs(self):
        with pytest.raises(IngestionRefusedError, match="INGEST_BASE_URL"):
            read_required_environment_value({}, "INGEST_BASE_URL", "name the mount")
