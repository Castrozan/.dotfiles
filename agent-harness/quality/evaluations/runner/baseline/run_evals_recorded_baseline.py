import json
from datetime import datetime, timezone

from runner.baseline.run_evals_baseline import (
    baseline_pass_rate_failures,
    compliance_passed_and_total,
)
from runner.baseline.run_evals_baseline_history import (
    baseline_regression_failure,
    baseline_staleness_failure,
    previous_committed_baseline_pass_rate,
)
from runner.baseline.run_evals_baseline_policy import (
    baseline_test_evidence_status,
    recorded_baseline_policy_failures,
)
from runner.baseline.run_evals_baseline_reporting import (
    BaselineCheckSummary,
    print_baseline_failures,
    print_baseline_summary,
)
from runner.baseline.run_evals_baseline_store import BASELINE_PATH
from runner.baseline.run_evals_baseline_thresholds import (
    MAXIMUM_BASELINE_AGE_DAYS,
    MAXIMUM_REGRESSION_DROP,
)
from runner.baseline.run_evals_fingerprint import evaluation_category_names
from runner.baseline.run_evals_impact import evaluation_test_fingerprints
from runner.baseline.run_evals_recorded_results import (
    recorded_baseline_integrity_failures,
)
from runner.run_evals_configuration_contract import evaluation_configuration_failures


def check_recorded_baseline(expected_execution_profile: dict, config: dict) -> bool:
    if not BASELINE_PATH.exists():
        print_baseline_failures(["No committed evaluation baseline found"])
        return False
    baseline = json.loads(BASELINE_PATH.read_text())
    failures = evaluation_configuration_failures(config)
    failures.extend(recorded_baseline_integrity_failures(baseline))
    if failures:
        print_baseline_failures(failures)
        return False
    current_fingerprints = evaluation_test_fingerprints(config)
    evidence_status = baseline_test_evidence_status(baseline, current_fingerprints)
    failures = recorded_baseline_policy_failures(
        baseline,
        current_fingerprints,
        evaluation_category_names(),
        expected_execution_profile,
    )
    compliance_passed, compliance_total = compliance_passed_and_total(
        baseline["categories"]
    )
    failures.extend(
        baseline_pass_rate_failures(
            baseline["total_passed"],
            baseline["total_tests"],
            compliance_passed,
            compliance_total,
        )
    )
    previous_pass_rate = previous_committed_baseline_pass_rate(
        expected_execution_profile
    )
    regression = baseline_regression_failure(
        baseline["pass_rate"], previous_pass_rate, MAXIMUM_REGRESSION_DROP
    )
    if regression:
        failures.append(regression)
    _print_recorded_evidence(
        baseline, current_fingerprints, evidence_status, previous_pass_rate
    )
    if failures:
        print_baseline_failures(failures)
        return False
    print("\nPASSED: Recorded evaluation results meet regression thresholds.")
    print(
        "Current model behavior was not measured; pending evidence remains unmeasured."
    )
    return True


def _print_recorded_evidence(
    baseline: dict,
    current_fingerprints: dict,
    evidence_status: dict,
    previous_pass_rate: float | None,
) -> None:
    current_categories = _current_result_categories(baseline, evidence_status["fresh"])
    current_passed = sum(bucket["passed"] for bucket in current_categories.values())
    current_total = len(evidence_status["fresh"])
    compliance_passed, compliance_total = compliance_passed_and_total(
        current_categories
    )
    generated_at = datetime.fromisoformat(baseline["generated_at"])
    age_days = (datetime.now(timezone.utc) - generated_at).days
    print_baseline_summary(
        BaselineCheckSummary(
            baseline,
            age_days,
            current_passed,
            current_total,
            evidence_status,
            current_fingerprints,
            compliance_passed,
            compliance_total,
            previous_pass_rate,
            baseline["pass_rate"],
        )
    )
    refresh = baseline_staleness_failure(age_days, MAXIMUM_BASELINE_AGE_DAYS)
    if refresh:
        print(f"Measurement refresh required: {refresh}")


def _current_result_categories(baseline: dict, fresh: set[str]) -> dict:
    categories = {}
    for category, bucket in baseline["categories"].items():
        entries = [
            entry
            for entry in bucket["tests"]
            if f"{category}::{entry['name']}" in fresh
        ]
        passed = sum(entry["passed"] for entry in entries)
        categories[category] = {"passed": passed, "failed": len(entries) - passed}
    return categories
