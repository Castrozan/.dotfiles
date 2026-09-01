REQUIRED_BASELINE_CATEGORIES = {
    "communication",
    "skills/humanize/reader_recovery",
}
REQUIRED_HUMANIZE_PROFILE = "skills/humanize/reader_recovery"
MINIMUM_HUMANIZE_PROFILE_EPOCHS = 3
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


def preserved_evidence_profiles(
    baseline: dict,
    current_fingerprints: dict[str, str],
    execution_profile: dict,
) -> dict:
    return {
        name: profile
        for name, profile in baseline.get("evidence_profiles", {}).items()
        if profile.get("fingerprints") == current_fingerprints
        and profile.get("execution_profile") == execution_profile
    }


def baseline_evidence_failures(
    baseline: dict,
    current_test_fingerprints: dict[str, str],
    current_humanize_fingerprints: dict[str, str],
    current_categories: set[str],
    expected_execution_profile: dict,
) -> list[str]:
    failures = []
    if baseline.get("execution_profile") != expected_execution_profile:
        failures.append(
            "Baseline execution profile does not match the expected profile"
        )
    recorded_categories = set(baseline.get("categories", {}))
    missing_inventory = current_categories - recorded_categories
    obsolete_inventory = recorded_categories - current_categories
    if missing_inventory:
        failures.append(
            "Baseline is missing current evaluation categories: "
            + ", ".join(sorted(missing_inventory))
        )
    if obsolete_inventory:
        failures.append(
            "Baseline contains obsolete evaluation categories: "
            + ", ".join(sorted(obsolete_inventory))
        )
    recorded_test_fingerprints = {
        f"{category_name}::{test['name']}": test.get("fingerprint")
        for category_name, bucket in baseline.get("categories", {}).items()
        for test in bucket.get("tests", [])
    }
    current_test_keys = set(current_test_fingerprints)
    recorded_test_keys = set(recorded_test_fingerprints)
    missing_tests = current_test_keys - recorded_test_keys
    obsolete_tests = recorded_test_keys - current_test_keys
    stale_tests = {
        key
        for key in current_test_keys & recorded_test_keys
        if recorded_test_fingerprints[key] != current_test_fingerprints[key]
    }
    if missing_tests:
        failures.append(
            "Baseline is missing current evaluation tests: "
            + ", ".join(sorted(missing_tests))
        )
    if obsolete_tests:
        failures.append(
            "Baseline contains obsolete evaluation tests: "
            + ", ".join(sorted(obsolete_tests))
        )
    if stale_tests:
        failures.append(
            "Baseline contains stale evaluation tests: "
            + ", ".join(sorted(stale_tests))
        )
    missing_categories = REQUIRED_BASELINE_CATEGORIES - set(
        baseline.get("categories", {})
    )
    if missing_categories:
        failures.append(
            "Baseline is missing required categories: "
            + ", ".join(sorted(missing_categories))
        )
    for category_name in REQUIRED_BASELINE_CATEGORIES - missing_categories:
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

    profile = baseline.get("evidence_profiles", {}).get(REQUIRED_HUMANIZE_PROFILE)
    if not profile:
        failures.append("Baseline is missing the repeated Humanize recovery profile")
        return failures
    if profile.get("execution_profile") != expected_execution_profile:
        failures.append(
            "Humanize recovery execution profile does not match the expected profile"
        )
    if profile.get("epochs", 0) < MINIMUM_HUMANIZE_PROFILE_EPOCHS:
        failures.append(
            "Humanize recovery profile needs at least "
            f"{MINIMUM_HUMANIZE_PROFILE_EPOCHS} epochs"
        )
    if profile.get("candidate_pass_rate", 0) < 0.9:
        failures.append("Humanize recovery candidate pass rate is below 90%")
    if profile.get("delta", -1) < 0:
        failures.append("Humanize recovery candidate trails its Git-ref control")
    if profile.get("candidate_hard_failures"):
        failures.append("Humanize recovery profile contains a hard-failed case")
    if profile.get("fingerprints") != current_humanize_fingerprints:
        failures.append("Humanize recovery profile does not match the current source")
    return failures
