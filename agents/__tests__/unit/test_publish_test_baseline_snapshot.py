import re

from publish_test_baseline_snapshot import (
    DOTFILES_TEST_BASELINE_SCHEMA_VERSION,
    DOTFILES_TEST_BASELINE_TOPIC,
    build_ingestion_event,
    build_test_baseline_payload,
    resolve_event_source,
)

BASELINE_DOCUMENT = {
    "generated_at": "2026-07-24T03:26:24.774576+00:00",
    "git_commit": "5667c9f6",
    "total_tests": 3,
    "total_passed": 2,
    "total_failed": 1,
    "pass_rate": 0.6667,
    "categories": {
        "skills/nix/repo": {
            "passed": 1,
            "failed": 1,
            "tests": [
                {"name": "rebuild_is_run_by_the_agent", "passed": True},
                {"name": "rebuild_is_never_deferred", "passed": False},
            ],
        },
        "adversarial": {
            "passed": 1,
            "failed": 0,
            "tests": [{"name": "mass_staging_is_blocked", "passed": True}],
        },
    },
}


class TestBaselineDocumentIsMappedOntoTheContractPayload:
    def test_maps_every_run_total_onto_its_contracted_field_name(self):
        payload = build_test_baseline_payload(BASELINE_DOCUMENT)

        assert payload["recordedAt"] == "2026-07-24T03:26:24.774576+00:00"
        assert payload["commit"] == "5667c9f6"
        assert payload["totalTests"] == 3
        assert payload["passedTests"] == 2
        assert payload["failedTests"] == 1
        assert payload["passRate"] == 0.6667

    def test_turns_the_category_map_into_a_stably_ordered_array(self):
        payload = build_test_baseline_payload(BASELINE_DOCUMENT)

        assert [entry["category"] for entry in payload["categories"]] == [
            "adversarial",
            "skills/nix/repo",
        ]

    def test_carries_each_category_tally_and_its_listed_tests(self):
        payload = build_test_baseline_payload(BASELINE_DOCUMENT)
        gated_category = payload["categories"][1]

        assert gated_category["passed"] == 1
        assert gated_category["failed"] == 1
        assert gated_category["tests"] == [
            {"name": "rebuild_is_run_by_the_agent", "passed": True},
            {"name": "rebuild_is_never_deferred", "passed": False},
        ]

    def test_emits_no_key_the_contract_does_not_declare(self):
        payload = build_test_baseline_payload(BASELINE_DOCUMENT)

        assert set(payload) == {
            "recordedAt",
            "commit",
            "totalTests",
            "passedTests",
            "failedTests",
            "passRate",
            "categories",
        }
        assert set(payload["categories"][0]) == {
            "category",
            "passed",
            "failed",
            "tests",
        }


class TestIngestionEnvelopeMatchesTheTopicContract:
    def test_stamps_the_topic_and_schema_version_the_api_serves(self):
        event = build_ingestion_event(BASELINE_DOCUMENT, "dotfiles-ci", None)

        assert event["topic"] == DOTFILES_TEST_BASELINE_TOPIC
        assert event["schemaVersion"] == DOTFILES_TEST_BASELINE_SCHEMA_VERSION
        assert event["producer"] == "dotfiles-ci"

    def test_produces_a_utc_timestamp_the_contract_pattern_accepts(self):
        event = build_ingestion_event(BASELINE_DOCUMENT, "dotfiles-ci", None)

        assert re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z", event["producedAt"]
        )

    def test_omits_the_source_object_entirely_when_no_run_context_exists(self):
        event = build_ingestion_event(BASELINE_DOCUMENT, "dotfiles-ci", None)

        assert "source" not in event

    def test_carries_the_run_context_when_the_producer_resolves_one(self):
        source = {"repository": "owner/dotfiles", "commit": "5667c9f6"}
        event = build_ingestion_event(BASELINE_DOCUMENT, "dotfiles-ci", source)

        assert event["source"] == source


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
