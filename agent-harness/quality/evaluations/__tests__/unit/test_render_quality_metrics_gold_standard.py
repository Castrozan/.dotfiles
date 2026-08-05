import json
from pathlib import Path

import pytest
from gold_standard_evidence_fixtures import (
    build_synthetic_evidence_repository,
    practice_named,
    write_document,
)
from render_quality_metrics_gold_standard import (
    GOLD_STANDARD_PRACTICE_COUNT,
    measure_gold_standard_practices,
)
from run_evals_baseline_thresholds import (
    MAXIMUM_BASELINE_AGE_DAYS,
    MAXIMUM_REGRESSION_DROP,
)

REPOSITORY_ROOT_OF_THE_LIVE_CHECKOUT = Path(__file__).resolve().parents[5]
PRACTICES_NOT_MEASURED_FROM_THE_CHECKOUT = {
    "regression-gating",
    "baseline-freshness-gating",
}


@pytest.fixture
def synthetic_repository_root(tmp_path):
    return build_synthetic_evidence_repository(tmp_path)


class TestPracticesAreMeasuredFromCommittedEvidenceNotAsserted:
    def test_every_registered_practice_is_reported_once(
        self, synthetic_repository_root
    ):
        practices = measure_gold_standard_practices(synthetic_repository_root)
        assert len(practices) == GOLD_STANDARD_PRACTICE_COUNT
        assert len({practice["practice"] for practice in practices}) == len(practices)

    def test_rubric_grading_counts_judged_suites_against_every_discovered_suite(
        self, synthetic_repository_root
    ):
        practice = practice_named(
            measure_gold_standard_practices(synthetic_repository_root),
            "rubric-graded-judging",
        )
        assert practice["measurement"] == 2
        assert practice["measurementUnit"] == "of 4 eval suites"
        assert practice["adopted"] is True

    def test_judge_calibration_reports_the_recorded_agreement(
        self, synthetic_repository_root
    ):
        practice = practice_named(
            measure_gold_standard_practices(synthetic_repository_root),
            "judge-calibration",
        )
        assert practice["measurement"] == 0.833
        assert practice["measurementUnit"] == "Cohen's kappa over 24 labelled cases"
        assert practice["adopted"] is True

    def test_agreement_below_the_substantial_threshold_is_not_adopted(
        self, synthetic_repository_root
    ):
        write_document(
            synthetic_repository_root
            / "agent-harness/quality/evaluations/calibration/judge_calibration.yaml",
            "recorded_agreement:\n  cases: 24\n  cohens_kappa: 0.41\n",
        )
        practice = practice_named(
            measure_gold_standard_practices(synthetic_repository_root),
            "judge-calibration",
        )
        assert practice["adopted"] is False

    def test_adversarial_testing_counts_the_cases_in_the_injection_suite(
        self, synthetic_repository_root
    ):
        practice = practice_named(
            measure_gold_standard_practices(synthetic_repository_root),
            "adversarial-testing",
        )
        assert practice["measurement"] == 2
        assert practice["adopted"] is True

    def test_a_single_epoch_baseline_reports_sampling_as_not_adopted(
        self, synthetic_repository_root
    ):
        practice = practice_named(
            measure_gold_standard_practices(synthetic_repository_root),
            "repeated-sampling",
        )
        assert practice["measurement"] == 1
        assert practice["adopted"] is False

    def test_a_sampled_baseline_reports_its_epochs(self, synthetic_repository_root):
        write_document(
            synthetic_repository_root
            / "agent-harness/quality/evaluations/baseline.json",
            json.dumps({"pass_rate": 0.9, "sampling": {"epochs": 5}}),
        )
        practice = practice_named(
            measure_gold_standard_practices(synthetic_repository_root),
            "repeated-sampling",
        )
        assert practice["measurement"] == 5
        assert practice["adopted"] is True

    def test_paired_significance_sums_the_paired_tests_across_categories(
        self, synthetic_repository_root
    ):
        practice = practice_named(
            measure_gold_standard_practices(synthetic_repository_root),
            "paired-significance",
        )
        assert practice["measurement"] == 20
        assert practice["adopted"] is True

    def test_the_gates_report_the_thresholds_that_actually_fail_ci(
        self, synthetic_repository_root
    ):
        practices = measure_gold_standard_practices(synthetic_repository_root)
        regression = practice_named(practices, "regression-gating")
        freshness = practice_named(practices, "baseline-freshness-gating")
        assert regression["measurement"] == round(MAXIMUM_REGRESSION_DROP * 100, 2)
        assert freshness["measurement"] == MAXIMUM_BASELINE_AGE_DAYS
        assert regression["adopted"] is True
        assert freshness["adopted"] is True


class TestEvidenceMissingFromTheCheckoutIsReportedNotGuessed:
    def test_an_empty_checkout_reports_every_measured_practice_as_unadopted(
        self, tmp_path
    ):
        measured = [
            practice
            for practice in measure_gold_standard_practices(tmp_path)
            if practice["practice"] not in PRACTICES_NOT_MEASURED_FROM_THE_CHECKOUT
        ]
        assert measured
        assert all(practice["adopted"] is False for practice in measured)
        assert all(practice["measurement"] == 0 for practice in measured)


class TestTheLiveCheckoutIsMeasurable:
    def test_every_practice_carries_a_renderable_evidence_sentence(self):
        practices = measure_gold_standard_practices(
            REPOSITORY_ROOT_OF_THE_LIVE_CHECKOUT
        )
        assert len(practices) == GOLD_STANDARD_PRACTICE_COUNT
        for practice in practices:
            assert set(practice) == {
                "practice",
                "adopted",
                "measurement",
                "measurementUnit",
                "evidence",
            }
            assert practice["evidence"].endswith(".")
            assert practice["measurementUnit"]
