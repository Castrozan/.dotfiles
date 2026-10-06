from typing import NamedTuple

from runner.baseline.run_evals_baseline_thresholds import (
    MAXIMUM_BASELINE_AGE_DAYS,
    MINIMUM_PASS_RATE_COMPLIANCE,
)
from runner.sampling.run_evals_statistics import (
    format_pass_rate_with_confidence_interval,
    wilson_score_interval,
)


class BaselineCheckSummary(NamedTuple):
    baseline: dict
    age_days: int
    current_passed: int
    current_total: int
    evidence_status: dict
    current_test_fingerprints: dict
    compliance_passed: int
    compliance_total: int
    previous_pass_rate: float | None
    materialized_pass_rate: float


def print_baseline_summary(summary: BaselineCheckSummary) -> None:
    baseline = summary.baseline
    print("=" * 60)
    print("EVAL BASELINE CHECK")
    print("=" * 60)
    print(f"  Generated: {baseline['generated_at']}")
    print(
        "  Oldest evidence: "
        f"{baseline.get('oldest_evidence_at', baseline['generated_at'])}"
    )
    print(
        f"  Age: {summary.age_days} days (freshness window {MAXIMUM_BASELINE_AGE_DAYS})"
    )
    print(f"  Commit: {baseline.get('git_commit', 'unknown')}")
    print(
        "  "
        + format_pass_rate_with_confidence_interval(
            summary.current_passed, summary.current_total
        )
    )
    if summary.compliance_total > 0:
        _print_compliance_interval(summary.compliance_passed, summary.compliance_total)
    if summary.previous_pass_rate is not None:
        print(
            f"  Previous baseline: {summary.previous_pass_rate:.1%} "
            f"(delta {summary.materialized_pass_rate - summary.previous_pass_rate:+.1%})"
        )
    print(
        f"  Recorded results: {baseline['total_passed']}/{baseline['total_tests']} "
        f"({summary.materialized_pass_rate:.1%})"
    )
    print(
        f"  Current evidence: {summary.current_passed}/{summary.current_total} "
        f"passed across {len(summary.evidence_status['fresh'])}/"
        f"{len(summary.current_test_fingerprints)} tests"
    )
    print(
        f"  Pending evidence: {len(summary.evidence_status['stale'])} stale, "
        f"{len(summary.evidence_status['missing'])} missing"
    )
    _print_sampling_summary(baseline.get("sampling"))


def _print_compliance_interval(compliance_passed: int, compliance_total: int) -> None:
    compliance_lower, compliance_upper = wilson_score_interval(
        compliance_passed, compliance_total
    )
    print(
        f"  Compliance: {compliance_passed / compliance_total:.1%} "
        f"(95% Wilson CI {compliance_lower:.1%} to {compliance_upper:.1%}, "
        f"floor {MINIMUM_PASS_RATE_COMPLIANCE:.0%})"
    )


def _print_sampling_summary(sampling: dict | None) -> None:
    if sampling:
        pass_at_2 = sampling.get("suite_pass_at_2")
        pass_at_2_text = f", pass@2 {pass_at_2:.1%}" if pass_at_2 is not None else ""
        print(
            f"  Sampling: {sampling['epochs']} epochs, "
            f"{sampling['total_samples']} samples, "
            f"pass@1 {sampling['suite_pass_at_1']:.1%}{pass_at_2_text}, "
            f"flaky {len(sampling['flaky_tests'])}"
        )


def print_baseline_failures(failures: list[str]) -> None:
    print(f"\nFAILED ({len(failures)} issues):")
    for failure in failures:
        print(f"  - {failure}")
