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
    "oldest_evidence_at": "2026-07-20T03:26:24.774576+00:00",
    "minimum_current_evidence": 2,
    "execution_profile": {
        "subject": {
            "harness": "codex",
            "model": "gpt-5.6-sol",
            "reasoning_effort": "high",
        },
        "judge": {
            "harness": "codex",
            "model": "gpt-5.6-luna",
            "reasoning_effort": "low",
        },
    },
    "execution_profiles": {
        "codex-profile": {
            "subject": {
                "harness": "codex",
                "model": "gpt-5.6-sol",
                "reasoning_effort": "high",
            },
            "judge": {
                "harness": "codex",
                "model": "gpt-5.6-luna",
                "reasoning_effort": "low",
            },
        }
    },
    "token_usage": {
        "subject": {
            "codex": {
                "invocations": 2,
                "measured_invocations": 2,
                "input_tokens": 120,
                "cached_input_tokens": 80,
                "cache_write_input_tokens": 0,
                "output_tokens": 20,
                "reasoning_output_tokens": 5,
            }
        }
    },
    "categories": {
        "skills/nix/repo": {
            "passed": 1,
            "failed": 1,
            "tests": [
                {
                    "name": "rebuild_is_run_by_the_agent",
                    "passed": True,
                    "fingerprint": "first-sha",
                    "generated_at": "2026-07-24T03:26:24.774576+00:00",
                    "execution_profile_id": "codex-profile",
                    "run_source": {"kind": "checkpoint", "git_commit": "5667c9f6"},
                },
                {
                    "name": "rebuild_is_never_deferred",
                    "passed": False,
                    "fingerprint": "second-sha",
                    "generated_at": "2026-07-20T03:26:24.774576+00:00",
                    "execution_profile_id": "codex-profile",
                    "run_source": {"kind": "recovered", "session_id": "session-1"},
                },
            ],
        },
        "adversarial": {
            "passed": 1,
            "failed": 0,
            "tests": [
                {
                    "name": "mass_staging_is_blocked",
                    "passed": True,
                    "fingerprint": "third-sha",
                    "generated_at": "2026-07-24T03:26:24.774576+00:00",
                    "execution_profile_id": "codex-profile",
                    "run_source": {"kind": "checkpoint", "git_commit": "5667c9f6"},
                }
            ],
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
        assert payload["oldestEvidenceAt"] == "2026-07-20T03:26:24.774576+00:00"
        assert payload["minimumCurrentEvidence"] == 2

    def test_carries_execution_profiles_and_normalized_token_usage(self):
        payload = build_test_baseline_payload(BASELINE_DOCUMENT)

        assert payload["executionProfile"]["subject"]["reasoningEffort"] == "high"
        assert payload["executionProfiles"][0]["id"] == "codex-profile"
        assert payload["tokenUsage"]["subject"]["codex"] == {
            "invocations": 2,
            "measuredInvocations": 2,
            "inputTokens": 120,
            "cachedInputTokens": 80,
            "cacheWriteInputTokens": 0,
            "outputTokens": 20,
            "reasoningOutputTokens": 5,
        }

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
            {
                "name": "rebuild_is_run_by_the_agent",
                "passed": True,
                "fingerprint": "first-sha",
                "generatedAt": "2026-07-24T03:26:24.774576+00:00",
                "executionProfileId": "codex-profile",
                "runSource": {"kind": "checkpoint", "gitCommit": "5667c9f6"},
            },
            {
                "name": "rebuild_is_never_deferred",
                "passed": False,
                "fingerprint": "second-sha",
                "generatedAt": "2026-07-20T03:26:24.774576+00:00",
                "executionProfileId": "codex-profile",
                "runSource": {"kind": "recovered", "sessionId": "session-1"},
            },
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
            "oldestEvidenceAt",
            "minimumCurrentEvidence",
            "executionProfile",
            "executionProfiles",
            "tokenUsage",
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
