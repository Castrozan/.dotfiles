import pytest

from reporting import run_evals_reporting as reporting
from runner.execution.run_evals_test_runner import TestResult


def test_results_report_preserves_failures_output_and_duration(capsys):
    results = [
        TestResult("pass", True, 1, "", []),
        TestResult("assertion", False, 2, "actual", ["expected another value"]),
        TestResult("error", False, 3, "", [], error="timeout"),
    ]
    assert not reporting.print_results(results, "codex")
    output = capsys.readouterr().out
    for fragment in [
        "RESULTS (codex)",
        "expected another value",
        "Output: actual",
        "Error: timeout",
        "Passed: 1/3",
        "Failed: 2/3",
        "Total time: 6.0s",
    ]:
        assert fragment in output
    assert reporting.print_results(results[:1])
    assert reporting.print_results([])


def test_sampling_summary_distinguishes_flaky_and_hard_failures(capsys):
    samples = [
        {
            "name": "stable",
            "passes": 2,
            "total": 2,
            "flaky": False,
            "lower": 0.3,
            "upper": 1,
        },
        {
            "name": "flaky",
            "passes": 1,
            "total": 2,
            "flaky": True,
            "lower": 0.1,
            "upper": 0.9,
        },
        {
            "name": "failed",
            "passes": 0,
            "total": 2,
            "flaky": False,
            "lower": 0,
            "upper": 0.7,
        },
    ]
    assert not reporting.print_epoch_summary(samples, 2)
    output = capsys.readouterr().out
    assert "[FLAKY] flaky: 1/2" in output and "[FAIL] failed: 0/2" in output
    assert "suite pass@2:" in output and "hard-failed: 1" in output
    assert reporting.print_epoch_summary(samples[:2], 1)
    assert "suite pass@2:" not in capsys.readouterr().out


@pytest.mark.parametrize("method", ["mcnemar_exact", "paired_bootstrap"])
@pytest.mark.parametrize(
    "significant,delta,passed",
    [(True, 0.2, True), (False, 0.2, False), (True, -0.2, False)],
)
def test_comparison_gate_requires_positive_significant_difference(
    capsys, method, significant, delta, passed
):
    comparison = dict(
        n_paired=10,
        variant_a_pass_rate=0.8,
        variant_b_pass_rate=0.6,
        delta=delta,
        method=method,
        a_only_wins=3,
        b_only_wins=1,
        p_value=0.03,
        significant=significant,
        epochs=3,
        sample_pairs=30,
        lower_bound=-0.1,
        upper_bound=0.4,
    )
    assert reporting.print_ab_summary(comparison) == passed
    output = capsys.readouterr().out
    assert "Paired tests: 10" in output and "Candidate: 80.0%" in output
    assert ("McNemar" in output) == (method == "mcnemar_exact")


def test_calibration_reports_confusion_and_disagreements(capsys):
    agreement = dict(
        n=4,
        agreements=2,
        accuracy=0.5,
        cohens_kappa=0,
        balanced_accuracy=0.5,
        failed_case_recall=0.5,
        confusion_matrix=dict(tp=1, tn=1, fp=1, fn=1),
        by_family={
            "routing": dict(
                balanced_accuracy=0.5, failed_case_recall=0.5, cohens_kappa=0
            )
        },
        disagreements=[
            dict(name="false pass", human=False, judge=True, reason="missed"),
            dict(name="false fail", human=True, judge=False, reason="extra"),
        ],
        meets_gate=False,
    )
    assert not reporting.print_calibration_summary(agreement)
    output = capsys.readouterr().out
    assert "Confusion: TP 1, TN 1, FP 1, FN 1" in output
    assert "human=FAIL judge=PASS (missed)" in output
    assert "human=PASS judge=FAIL (extra)" in output
    agreement.update(meets_gate=True, disagreements=[])
    assert reporting.print_calibration_summary(agreement)
    assert "Disagreements:" not in capsys.readouterr().out


def test_usage_and_category_listing_preserve_counts(capsys):
    reporting.print_provider_usage({})
    assert capsys.readouterr().out == ""
    reporting.print_provider_usage(
        {
            "subject": {
                "codex": dict(
                    invocations=2,
                    input_tokens=30,
                    cached_input_tokens=10,
                    output_tokens=8,
                    reasoning_output_tokens=3,
                )
            }
        }
    )
    assert (
        "subject/codex: 2 invocations, 30 input (10 cached), 8 output (3 reasoning)"
        in capsys.readouterr().out
    )
    reporting.list_categories(
        {"tests": {"routing": [{"name": "skill"}]}, "smoke_test": {"name": "alive"}}
    )
    output = capsys.readouterr().out
    assert "routing (1 tests)" in output and "- skill" in output and "- alive" in output
