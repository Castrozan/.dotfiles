import json
from datetime import datetime, timezone

from runner.baseline.run_evals_baseline_history import (
    baseline_regression_failure,
    baseline_staleness_failure,
    previous_committed_baseline_pass_rate,
)
from runner.baseline.run_evals_baseline_policy import (
    baseline_evidence_failures,
    baseline_test_evidence_status,
    compliance_passed_and_total as policy_compliance_passed_and_total,
)
from runner.baseline.run_evals_baseline_record import (
    BASELINE_PATH,
)
from runner.baseline.run_evals_baseline_thresholds import (
    COMPLIANCE_CATEGORIES,
    MAXIMUM_BASELINE_AGE_DAYS,
    MAXIMUM_REGRESSION_DROP,
    MINIMUM_PASS_RATE_COMPLIANCE,
    MINIMUM_PASS_RATE_OVERALL,
)
from runner.baseline import run_evals_baseline_reporting
from runner.baseline.run_evals_fingerprint import (
    evaluation_category_names,
)
from runner.baseline.run_evals_impact import evaluation_test_fingerprints


def compliance_passed_and_total(categories: dict) -> tuple[int, int]:
    return policy_compliance_passed_and_total(categories, COMPLIANCE_CATEGORIES)


def check_baseline_for_regression(
    expected_execution_profile: dict, config: dict
) -> bool:
    if not BASELINE_PATH.exists():
        print(
            "FAIL: No baseline file found at agent-harness/quality/evaluations/baseline.json"
        )
        print("  Run 'run-evals.py --save-baseline' locally to generate it.")
        return False

    with open(BASELINE_PATH) as f:
        baseline = json.load(f)

    current_test_fingerprints = evaluation_test_fingerprints(config)
    evidence_status = baseline_test_evidence_status(baseline, current_test_fingerprints)
    recorded_entries = {
        f"{category_name}::{test['name']}": (category_name, test)
        for category_name, bucket in baseline.get("categories", {}).items()
        for test in bucket.get("tests", [])
    }
    current_categories = _current_evidence_categories(evidence_status, recorded_entries)
    failures = []
    failures.extend(
        baseline_evidence_failures(
            baseline,
            current_test_fingerprints,
            evaluation_category_names(),
            expected_execution_profile,
        )
    )

    generated_at = datetime.fromisoformat(baseline["generated_at"])
    age_days = (datetime.now(timezone.utc) - generated_at).days

    current_passed, current_total = _evidence_totals(current_categories)
    compliance_passed, compliance_total = compliance_passed_and_total(
        current_categories
    )
    _append_pass_rate_failures(
        current_passed,
        current_total,
        compliance_passed,
        compliance_total,
        failures,
    )

    materialized_pass_rate = baseline.get("pass_rate", 0)
    previous_pass_rate = previous_committed_baseline_pass_rate(
        expected_execution_profile
    )
    regression = baseline_regression_failure(
        materialized_pass_rate, previous_pass_rate, MAXIMUM_REGRESSION_DROP
    )
    staleness = baseline_staleness_failure(age_days, MAXIMUM_BASELINE_AGE_DAYS)
    _append_history_failures(regression, staleness, failures)
    run_evals_baseline_reporting.print_baseline_summary(
        run_evals_baseline_reporting.BaselineCheckSummary(
            baseline,
            age_days,
            current_passed,
            current_total,
            evidence_status,
            current_test_fingerprints,
            compliance_passed,
            compliance_total,
            previous_pass_rate,
            materialized_pass_rate,
        )
    )

    if failures:
        run_evals_baseline_reporting.print_baseline_failures(failures)
        return False

    print("\nPASSED: Baseline meets all thresholds.")
    return True


def _current_evidence_categories(evidence_status: dict, recorded_entries: dict) -> dict:
    current_categories = {}
    for key in evidence_status["fresh"]:
        category_name, test = recorded_entries[key]
        bucket = current_categories.setdefault(
            category_name, {"passed": 0, "failed": 0}
        )
        bucket["passed" if test["passed"] else "failed"] += 1
    return current_categories


def _evidence_totals(current_categories: dict) -> tuple[int, int]:
    current_passed = sum(bucket["passed"] for bucket in current_categories.values())
    current_total = sum(
        bucket["passed"] + bucket["failed"] for bucket in current_categories.values()
    )
    return current_passed, current_total


def _append_pass_rate_failures(
    current_passed: int,
    current_total: int,
    compliance_passed: int,
    compliance_total: int,
    failures: list[str],
) -> None:
    overall_pass_rate = current_passed / current_total if current_total else 0
    if overall_pass_rate < MINIMUM_PASS_RATE_OVERALL:
        failures.append(
            f"Overall pass rate {overall_pass_rate:.1%} "
            f"below minimum {MINIMUM_PASS_RATE_OVERALL:.1%}"
        )
    if compliance_total > 0:
        compliance_rate = compliance_passed / compliance_total
        if compliance_rate < MINIMUM_PASS_RATE_COMPLIANCE:
            failures.append(
                f"Compliance pass rate {compliance_rate:.1%} "
                f"below minimum {MINIMUM_PASS_RATE_COMPLIANCE:.1%}"
            )


def _append_history_failures(
    regression: str | None, staleness: str | None, failures: list[str]
) -> None:
    if regression:
        failures.append(regression)
    if staleness:
        failures.append(staleness)
