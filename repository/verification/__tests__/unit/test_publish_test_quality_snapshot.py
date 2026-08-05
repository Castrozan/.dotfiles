from publish_test_quality_snapshot import (
    DOTFILES_TEST_QUALITY_SCHEMA_VERSION,
    DOTFILES_TEST_QUALITY_TOPIC,
    build_test_quality_payload,
)

QUALITY_METRICS_DOCUMENT = {
    "generatedAt": "2026-07-24T21:08:45.630094+00:00",
    "generatedCommit": "9a7b1f32",
    "staticEvals": {
        "totalTests": 163,
        "passedTests": 152,
        "passRate": 0.9325,
        "suiteCount": 15,
        "categoryCount": 23,
        "recordedAt": "2026-07-24T03:26:24.774576+00:00",
        "recordedCommit": "5667c9f6",
    },
    "integrationScenarioCount": 7,
    "endToEndScenarioCount": 34,
    "coreRules": {"lineCount": 165, "ruleBlockCount": 18},
    "hooks": {
        "wiredEvents": [
            "post-tool-use",
            "pre-tool-use",
            "session-start",
            "stop",
            "user-prompt-submit",
        ],
        "entryPointCount": 18,
    },
    "goldStandardPractices": [
        {
            "practice": "execution-graded-assertions",
            "adopted": True,
            "measurement": 0.62,
            "measurementUnit": "fraction",
            "evidence": "agents/evals/run_evals_assertions.py",
        }
    ],
    "instructionLoadingExperiment": {
        "recordedAt": "2026-07-23T22:35:02+00:00",
        "recordedCommit": "7659f816",
        "significanceAlpha": 0.05,
        "categories": [
            {
                "category": "workflow-compliance",
                "pairedTests": 8,
                "passRateWithInstructions": 1.0,
                "passRateWithoutInstructions": 0.625,
                "delta": 0.375,
                "instructionsOnlyWins": 3,
                "controlOnlyWins": 0,
                "exactPValue": 0.25,
                "significant": False,
            }
        ],
    },
}


class TestQualityMetricsAreMappedOntoTheContractPayload:
    def test_names_the_topic_and_schema_version_the_api_serves(self):
        assert DOTFILES_TEST_QUALITY_TOPIC == "dotfiles-test-quality"
        assert DOTFILES_TEST_QUALITY_SCHEMA_VERSION == 1

    def test_maps_the_render_stamp_onto_the_contracted_recorded_at(self):
        payload = build_test_quality_payload(QUALITY_METRICS_DOCUMENT, {})

        assert payload["recordedAt"] == "2026-07-24T21:08:45.630094+00:00"
        assert payload["commit"] == "9a7b1f32"

    def test_carries_the_eval_baseline_the_dashboard_headline_reads(self):
        payload = build_test_quality_payload(QUALITY_METRICS_DOCUMENT, {})

        assert payload["staticEvals"]["totalTests"] == 163
        assert payload["staticEvals"]["passedTests"] == 152
        assert payload["staticEvals"]["passRate"] == 0.9325
        assert payload["staticEvals"]["recordedCommit"] == "5667c9f6"

    def test_carries_every_pyramid_tier_the_dashboard_charts(self):
        payload = build_test_quality_payload(QUALITY_METRICS_DOCUMENT, {})

        assert payload["staticEvals"]["suiteCount"] == 15
        assert payload["integrationScenarioCount"] == 7
        assert payload["endToEndScenarioCount"] == 34

    def test_carries_the_instruction_surfaces_the_agents_load(self):
        payload = build_test_quality_payload(QUALITY_METRICS_DOCUMENT, {})

        assert payload["coreRules"] == {"lineCount": 165, "ruleBlockCount": 18}
        assert payload["hooks"]["entryPointCount"] == 18
        assert payload["hooks"]["wiredEvents"][0] == "post-tool-use"

    def test_carries_the_gold_standard_scorecard_the_dashboard_scores(self):
        payload = build_test_quality_payload(QUALITY_METRICS_DOCUMENT, {})

        assert payload["goldStandardPractices"] == [
            {
                "practice": "execution-graded-assertions",
                "adopted": True,
                "measurement": 0.62,
                "measurementUnit": "fraction",
                "evidence": "agents/evals/run_evals_assertions.py",
            }
        ]

    def test_carries_the_paired_instruction_loading_experiment(self):
        payload = build_test_quality_payload(QUALITY_METRICS_DOCUMENT, {})
        experiment = payload["instructionLoadingExperiment"]

        assert experiment["significanceAlpha"] == 0.05
        assert experiment["recordedCommit"] == "7659f816"
        assert experiment["categories"][0]["category"] == "workflow-compliance"
        assert experiment["categories"][0]["delta"] == 0.375

    def test_emits_no_key_the_contract_does_not_declare(self):
        payload = build_test_quality_payload(QUALITY_METRICS_DOCUMENT, {})

        assert set(payload) == {
            "recordedAt",
            "commit",
            "staticEvals",
            "integrationScenarioCount",
            "endToEndScenarioCount",
            "coreRules",
            "hooks",
            "goldStandardPractices",
            "instructionLoadingExperiment",
        }
        assert set(payload["goldStandardPractices"][0]) == {
            "practice",
            "adopted",
            "measurement",
            "measurementUnit",
            "evidence",
        }
        assert set(payload["instructionLoadingExperiment"]) == {
            "recordedAt",
            "recordedCommit",
            "significanceAlpha",
            "categories",
        }
        assert set(payload["staticEvals"]) == {
            "totalTests",
            "passedTests",
            "passRate",
            "suiteCount",
            "categoryCount",
            "recordedAt",
            "recordedCommit",
        }
        assert set(payload["hooks"]) == {"wiredEvents", "entryPointCount"}

    def test_leaves_a_renderer_added_key_out_of_the_published_event(self):
        document = {
            **QUALITY_METRICS_DOCUMENT,
            "skillCount": 21,
            "coreRules": {**QUALITY_METRICS_DOCUMENT["coreRules"], "wordCount": 2200},
        }

        payload = build_test_quality_payload(document, {})

        assert "skillCount" not in payload
        assert "wordCount" not in payload["coreRules"]
