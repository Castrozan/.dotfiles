import json
from datetime import datetime, timezone

from run_evals_baseline_history import (
    baseline_regression_failure,
    baseline_staleness_failure,
    previous_committed_baseline_pass_rate,
)
from run_evals_baseline_policy import (
    baseline_evidence_failures,
    compliance_passed_and_total as policy_compliance_passed_and_total,
)
from run_evals_baseline_record import (
    BASELINE_PATH,
)
from run_evals_baseline_thresholds import (
    COMPLIANCE_CATEGORIES,
    MAXIMUM_BASELINE_AGE_DAYS,
    MAXIMUM_REGRESSION_DROP,
    MINIMUM_PASS_RATE_COMPLIANCE,
    MINIMUM_PASS_RATE_OVERALL,
)
from run_evals_statistics import (
    format_pass_rate_with_confidence_interval,
    wilson_score_interval,
)
from run_evals_fingerprint import (
    evaluation_category_names,
    evaluation_fingerprints,
    humanize_recovery_fingerprints,
)


def compliance_passed_and_total(categories: dict) -> tuple[int, int]:
    return policy_compliance_passed_and_total(categories, COMPLIANCE_CATEGORIES)


def check_baseline_for_regression(expected_execution_profile: dict) -> bool:
    if not BASELINE_PATH.exists():
        print(
            "FAIL: No baseline file found at agent-harness/quality/evaluations/baseline.json"
        )
        print("  Run 'run-evals.py --save-baseline' locally to generate it.")
        return False

    with open(BASELINE_PATH) as f:
        baseline = json.load(f)

    failures = []
    failures.extend(
        baseline_evidence_failures(
            baseline,
            evaluation_fingerprints(),
            humanize_recovery_fingerprints(),
            evaluation_category_names(),
            expected_execution_profile,
        )
    )

    generated_at = datetime.fromisoformat(baseline["generated_at"])
    age_days = (datetime.now(timezone.utc) - generated_at).days

    overall_pass_rate = baseline.get("pass_rate", 0)
    if overall_pass_rate < MINIMUM_PASS_RATE_OVERALL:
        failures.append(
            f"Overall pass rate {overall_pass_rate:.1%} "
            f"below minimum {MINIMUM_PASS_RATE_OVERALL:.1%}"
        )

    compliance_passed, compliance_total = compliance_passed_and_total(
        baseline.get("categories", {})
    )
    if compliance_total > 0:
        compliance_rate = compliance_passed / compliance_total
        if compliance_rate < MINIMUM_PASS_RATE_COMPLIANCE:
            failures.append(
                f"Compliance pass rate {compliance_rate:.1%} "
                f"below minimum {MINIMUM_PASS_RATE_COMPLIANCE:.1%}"
            )

    previous_pass_rate = previous_committed_baseline_pass_rate(
        expected_execution_profile
    )
    regression = baseline_regression_failure(
        overall_pass_rate, previous_pass_rate, MAXIMUM_REGRESSION_DROP
    )
    if regression:
        failures.append(regression)

    staleness = baseline_staleness_failure(age_days, MAXIMUM_BASELINE_AGE_DAYS)
    if staleness:
        failures.append(staleness)

    print("=" * 60)
    print("EVAL BASELINE CHECK")
    print("=" * 60)
    print(f"  Generated: {baseline['generated_at']}")
    print(f"  Age: {age_days} days (freshness window {MAXIMUM_BASELINE_AGE_DAYS})")
    print(f"  Commit: {baseline.get('git_commit', 'unknown')}")
    print(
        "  "
        + format_pass_rate_with_confidence_interval(
            baseline["total_passed"], baseline["total_tests"]
        )
    )
    if compliance_total > 0:
        compliance_lower, compliance_upper = wilson_score_interval(
            compliance_passed, compliance_total
        )
        print(
            f"  Compliance: {compliance_passed / compliance_total:.1%} "
            f"(95% Wilson CI {compliance_lower:.1%} to {compliance_upper:.1%}, "
            f"floor {MINIMUM_PASS_RATE_COMPLIANCE:.0%})"
        )
    if previous_pass_rate is not None:
        print(
            f"  Previous baseline: {previous_pass_rate:.1%} "
            f"(delta {overall_pass_rate - previous_pass_rate:+.1%})"
        )
    print(f"  Tests: {baseline['total_passed']}/{baseline['total_tests']}")
    sampling = baseline.get("sampling")
    if sampling:
        pass_at_2 = sampling.get("suite_pass_at_2")
        pass_at_2_text = f", pass@2 {pass_at_2:.1%}" if pass_at_2 is not None else ""
        print(
            f"  Sampling: {sampling['epochs']} epochs, "
            f"{sampling['total_samples']} samples, "
            f"pass@1 {sampling['suite_pass_at_1']:.1%}{pass_at_2_text}, "
            f"flaky {len(sampling['flaky_tests'])}"
        )

    if failures:
        print(f"\nFAILED ({len(failures)} issues):")
        for failure in failures:
            print(f"  - {failure}")
        return False

    print("\nPASSED: Baseline meets all thresholds.")
    return True
