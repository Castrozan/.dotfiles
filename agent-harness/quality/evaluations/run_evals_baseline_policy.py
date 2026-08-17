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
    baseline: dict, current_fingerprints: dict[str, str]
) -> dict:
    return {
        name: profile
        for name, profile in baseline.get("evidence_profiles", {}).items()
        if profile.get("fingerprints") == current_fingerprints
    }


def baseline_evidence_failures(
    baseline: dict,
    current_fingerprints: dict[str, str],
    current_humanize_fingerprints: dict[str, str],
    current_categories: set[str],
) -> list[str]:
    failures = []
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

    recorded_fingerprints = baseline.get("fingerprints", {})
    for name, current_value in current_fingerprints.items():
        if recorded_fingerprints.get(name) != current_value:
            failures.append(
                f"Baseline {name} fingerprint does not match the current source"
            )

    profile = baseline.get("evidence_profiles", {}).get(REQUIRED_HUMANIZE_PROFILE)
    if not profile:
        failures.append("Baseline is missing the repeated Humanize recovery profile")
        return failures
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
