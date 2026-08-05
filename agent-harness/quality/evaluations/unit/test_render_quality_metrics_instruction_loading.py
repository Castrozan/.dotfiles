import json
from pathlib import Path

from render_quality_metrics_instruction_loading import (
    build_instruction_loading_experiment,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]

RECORDED_EXPERIMENT = {
    "generated_at": "2026-07-23T22:35:02+00:00",
    "git_commit": "7659f816",
    "significance_alpha": 0.05,
    "categories": {
        "workflow_compliance": {
            "paired_tests": 8,
            "pass_rate_with_instructions": 1.0,
            "pass_rate_without_instructions": 0.625,
            "delta": 0.375,
            "instructions_only_wins": 3,
            "control_only_wins": 0,
            "mcnemar_exact_p_value": 0.25,
            "significant": False,
        },
        "core_rules": {
            "paired_tests": 12,
            "pass_rate_with_instructions": 1.0,
            "pass_rate_without_instructions": 0.917,
            "delta": 0.083,
            "instructions_only_wins": 1,
            "control_only_wins": 0,
            "mcnemar_exact_p_value": 1.0,
            "significant": False,
        },
    },
}


def write_recorded_experiment(repository_root, experiment):
    experiment_path = (
        repository_root
        / "agent-harness/quality/evaluations/instruction-loading-experiment.json"
    )
    experiment_path.parent.mkdir(parents=True, exist_ok=True)
    experiment_path.write_text(json.dumps(experiment))
    return repository_root


class TestRecordedExperimentBecomesAContractedPayload:
    def test_renames_every_recorded_category_to_a_contracted_label(self, tmp_path):
        experiment = build_instruction_loading_experiment(
            write_recorded_experiment(tmp_path, RECORDED_EXPERIMENT)
        )

        assert [category["category"] for category in experiment["categories"]] == [
            "workflow-compliance",
            "core-rules",
        ]

    def test_carries_the_alpha_and_commit_the_verdicts_were_taken_at(self, tmp_path):
        experiment = build_instruction_loading_experiment(
            write_recorded_experiment(tmp_path, RECORDED_EXPERIMENT)
        )

        assert experiment["significanceAlpha"] == 0.05
        assert experiment["recordedCommit"] == "7659f816"
        assert experiment["recordedAt"] == "2026-07-23T22:35:02+00:00"

    def test_exposes_every_field_the_quality_contract_requires(self, tmp_path):
        experiment = build_instruction_loading_experiment(
            write_recorded_experiment(tmp_path, RECORDED_EXPERIMENT)
        )

        assert set(experiment) == {
            "recordedAt",
            "recordedCommit",
            "significanceAlpha",
            "categories",
        }
        assert set(experiment["categories"][0]) == {
            "category",
            "pairedTests",
            "passRateWithInstructions",
            "passRateWithoutInstructions",
            "delta",
            "instructionsOnlyWins",
            "controlOnlyWins",
            "exactPValue",
            "significant",
        }

    def test_carries_the_exact_test_p_value_under_its_contracted_name(self, tmp_path):
        experiment = build_instruction_loading_experiment(
            write_recorded_experiment(tmp_path, RECORDED_EXPERIMENT)
        )

        assert [category["exactPValue"] for category in experiment["categories"]] == [
            0.25,
            1.0,
        ]

    def test_carries_the_delta_the_two_arms_produce(self, tmp_path):
        experiment = build_instruction_loading_experiment(
            write_recorded_experiment(tmp_path, RECORDED_EXPERIMENT)
        )

        for category in experiment["categories"]:
            measured_delta = (
                category["passRateWithInstructions"]
                - category["passRateWithoutInstructions"]
            )
            assert abs(category["delta"] - measured_delta) <= 0.001


class TestCommittedExperimentIsRenderable:
    def test_renders_the_experiment_recorded_in_this_repository(self):
        experiment = build_instruction_loading_experiment(REPOSITORY_ROOT)

        assert experiment["categories"]
        assert 0 < experiment["significanceAlpha"] <= 1
        for category in experiment["categories"]:
            assert category["pairedTests"] > 0
            assert (
                category["instructionsOnlyWins"] + category["controlOnlyWins"]
                <= category["pairedTests"]
            )
            assert category["significant"] == (
                category["exactPValue"] <= experiment["significanceAlpha"]
            )
