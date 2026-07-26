from publish_test_baseline_snapshot import (
    DOTFILES_TEST_BASELINE_SCHEMA_VERSION,
    DOTFILES_TEST_BASELINE_TOPIC,
    build_test_baseline_payload,
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


class TestTopicIdentityMatchesTheRegisteredContract:
    def test_names_the_topic_and_schema_version_the_api_serves(self):
        assert DOTFILES_TEST_BASELINE_TOPIC == "dotfiles-test-baseline"
        assert DOTFILES_TEST_BASELINE_SCHEMA_VERSION == 1
