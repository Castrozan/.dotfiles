REQUIRED_BASELINE_CATEGORIES = {
    "communication",
}
MINIMUM_COMMUNICATION_PASS_RATE = 0.8


def compliance_passed_and_total(
    categories: dict, compliance_categories: set[str]
) -> tuple[int, int]:
    buckets = [
        bucket
        for category_name, bucket in categories.items()
        if category_name in compliance_categories
    ]
    passed = sum(bucket.get("passed", 0) for bucket in buckets)
    total = sum(bucket.get("passed", 0) + bucket.get("failed", 0) for bucket in buckets)
    return passed, total


def baseline_test_evidence_status(
    baseline: dict, current_test_fingerprints: dict[str, str]
) -> dict[str, set[str]]:
    recorded_test_fingerprints = {
        f"{category_name}::{test['name']}": test.get("fingerprint")
        for category_name, bucket in baseline.get("categories", {}).items()
        for test in bucket.get("tests", [])
    }
    current_test_keys = set(current_test_fingerprints)
    recorded_test_keys = set(recorded_test_fingerprints)
    shared_test_keys = current_test_keys & recorded_test_keys
    stale_tests = {
        key
        for key in shared_test_keys
        if recorded_test_fingerprints[key] != current_test_fingerprints[key]
    }
    return {
        "fresh": shared_test_keys - stale_tests,
        "missing": current_test_keys - recorded_test_keys,
        "obsolete": recorded_test_keys - current_test_keys,
        "stale": stale_tests,
    }


def baseline_evidence_failures(
    baseline: dict,
    current_test_fingerprints: dict[str, str],
    current_categories: set[str],
    expected_execution_profile: dict,
) -> list[str]:
    failures = recorded_baseline_policy_failures(
        baseline,
        current_test_fingerprints,
        current_categories,
        expected_execution_profile,
    )
    evidence_status = baseline_test_evidence_status(baseline, current_test_fingerprints)
    minimum_current_evidence = baseline.get("minimum_current_evidence", 1)
    if len(evidence_status["fresh"]) < minimum_current_evidence:
        failures.append(
            f"Current evaluation evidence covers {len(evidence_status['fresh'])} "
            f"tests, below the baseline floor of {minimum_current_evidence}"
        )
    return failures


def recorded_baseline_policy_failures(
    baseline: dict,
    current_test_fingerprints: dict[str, str],
    current_categories: set[str],
    expected_execution_profile: dict,
) -> list[str]:
    failures = []
    _append_inventory_evidence_failures(
        baseline,
        current_test_fingerprints,
        current_categories,
        expected_execution_profile,
        failures,
    )
    _append_required_category_failures(baseline, failures)
    return failures


def _append_inventory_evidence_failures(
    baseline: dict,
    current_test_fingerprints: dict[str, str],
    current_categories: set[str],
    expected_execution_profile: dict,
    failures: list[str],
) -> None:
    if baseline.get("execution_profile") != expected_execution_profile:
        failures.append(
            "Baseline execution profile does not match the expected profile"
        )
    recorded_categories = set(baseline.get("categories", {}))
    obsolete_inventory = recorded_categories - current_categories
    if obsolete_inventory:
        failures.append(
            "Baseline contains obsolete evaluation categories: "
            + ", ".join(sorted(obsolete_inventory))
        )
    evidence_status = baseline_test_evidence_status(baseline, current_test_fingerprints)
    if evidence_status["obsolete"]:
        failures.append(
            "Baseline contains obsolete evaluation tests: "
            + ", ".join(sorted(evidence_status["obsolete"]))
        )


def _append_required_category_failures(baseline: dict, failures: list[str]) -> None:
    present_required_categories = REQUIRED_BASELINE_CATEGORIES & set(
        baseline.get("categories", {})
    )
    for category_name in present_required_categories:
        bucket = baseline["categories"][category_name]
        total = bucket.get("passed", 0) + bucket.get("failed", 0)
        if total == 0:
            failures.append(f"Baseline category {category_name} contains no results")

    communication = baseline.get("categories", {}).get("communication", {})
    communication_total = communication.get("passed", 0) + communication.get(
        "failed", 0
    )
    if communication_total and (
        communication.get("passed", 0) / communication_total
        < MINIMUM_COMMUNICATION_PASS_RATE
    ):
        failures.append(
            f"Communication pass rate is below {MINIMUM_COMMUNICATION_PASS_RATE:.0%}"
        )

