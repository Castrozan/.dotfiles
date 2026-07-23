import json
import subprocess
from datetime import datetime, timezone

from run_evals_baseline_history import (
    baseline_regression_failure,
    previous_committed_baseline_pass_rate,
)
from run_evals_test_runner import TestResult
from run_evals_worktree_and_environment import REPO_ROOT

BASELINE_PATH = REPO_ROOT / "agents" / "evals" / "baseline.json"
MINIMUM_PASS_RATE_OVERALL = 0.75
MINIMUM_PASS_RATE_COMPLIANCE = 0.85
MAXIMUM_REGRESSION_DROP = 0.05
COMPLIANCE_CATEGORIES = {
    "instruction_compliance",
    "workflow_compliance",
    "rebuild_mandate",
    "delegation",
    "core_rules",
}


def compliance_passed_and_total(categories: dict) -> tuple[int, int]:
    passed = 0
    total = 0
    for category_name, bucket in categories.items():
        if category_name in COMPLIANCE_CATEGORIES:
            passed += bucket.get("passed", 0)
            total += bucket.get("passed", 0) + bucket.get("failed", 0)
    return passed, total


def get_current_git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def build_baseline_from_results(results: list[TestResult]) -> dict:
    categories = {}
    for result in results:
        category_name = result.category
        if category_name not in categories:
            categories[category_name] = {
                "passed": 0,
                "failed": 0,
                "tests": [],
            }
        categories[category_name]["tests"].append(
            {"name": result.name, "passed": result.passed}
        )
        if result.passed:
            categories[category_name]["passed"] += 1
        else:
            categories[category_name]["failed"] += 1

    total_passed = sum(1 for r in results if r.passed)
    total_tests = len(results)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": get_current_git_commit(),
        "total_tests": total_tests,
        "total_passed": total_passed,
        "total_failed": total_tests - total_passed,
        "pass_rate": (round(total_passed / total_tests, 4) if total_tests > 0 else 0),
        "categories": categories,
    }


def save_baseline(results: list[TestResult]) -> None:
    baseline = build_baseline_from_results(results)
    with open(BASELINE_PATH, "w") as f:
        json.dump(baseline, f, indent=2)
    print(f"\nBaseline saved to {BASELINE_PATH}")
    print(f"  Pass rate: {baseline['pass_rate']:.1%}")
    print(f"  Tests: {baseline['total_passed']}/{baseline['total_tests']}")
    print(f"  Commit: {baseline['git_commit']}")


def check_baseline_for_regression() -> bool:
    if not BASELINE_PATH.exists():
        print("FAIL: No baseline file found at agents/evals/baseline.json")
        print("  Run 'run-evals.py --save-baseline' locally to generate it.")
        return False

    with open(BASELINE_PATH) as f:
        baseline = json.load(f)

    failures = []

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

    previous_pass_rate = previous_committed_baseline_pass_rate()
    regression = baseline_regression_failure(
        overall_pass_rate, previous_pass_rate, MAXIMUM_REGRESSION_DROP
    )
    if regression:
        failures.append(regression)

    print("=" * 60)
    print("EVAL BASELINE CHECK")
    print("=" * 60)
    print(f"  Generated: {baseline['generated_at']}")
    print(f"  Age: {age_days} days")
    print(f"  Commit: {baseline.get('git_commit', 'unknown')}")
    print(f"  Pass rate: {overall_pass_rate:.1%}")
    if previous_pass_rate is not None:
        print(
            f"  Previous baseline: {previous_pass_rate:.1%} "
            f"(delta {overall_pass_rate - previous_pass_rate:+.1%})"
        )
    print(f"  Tests: {baseline['total_passed']}/{baseline['total_tests']}")

    if failures:
        print(f"\nFAILED ({len(failures)} issues):")
        for failure in failures:
            print(f"  - {failure}")
        return False

    print("\nPASSED: Baseline meets all thresholds.")
    return True
