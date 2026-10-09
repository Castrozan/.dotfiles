from collections import Counter


def recorded_baseline_integrity_failures(baseline: dict) -> list[str]:
    categories = baseline.get("categories", {})
    failures = [
        failure
        for category, bucket in categories.items()
        for failure in _category_integrity_failures(category, bucket)
    ]
    entries = [
        entry for bucket in categories.values() for entry in bucket.get("tests", [])
    ]
    return failures + _baseline_totals_failures(baseline, entries)


def _baseline_totals_failures(baseline: dict, entries: list[dict]) -> list[str]:
    passed = sum(entry.get("passed") is True for entry in entries)
    totals = {
        "total_tests": len(entries),
        "total_passed": passed,
        "total_failed": len(entries) - passed,
    }
    failures = _count_mismatches("Baseline", baseline, totals)
    pass_rate = round(passed / len(entries), 4) if entries else 0
    if not _recorded_pass_rate_matches(baseline.get("pass_rate"), pass_rate):
        failures.append("Baseline pass_rate does not match recorded outcomes")
    return failures + _recorded_coverage_failures(baseline, len(entries))


def _recorded_pass_rate_matches(recorded, expected: float) -> bool:
    return (
        isinstance(recorded, (int, float))
        and not isinstance(recorded, bool)
        and recorded == expected
    )


def _recorded_coverage_failures(baseline: dict, recorded_count: int) -> list[str]:
    minimum_evidence = baseline.get("minimum_current_evidence", 1)
    if not _valid_recorded_count(minimum_evidence):
        return ["Baseline evidence floor must be a nonnegative integer"]
    if recorded_count < minimum_evidence:
        return [
            f"Recorded evaluation evidence covers {recorded_count} tests, "
            f"below the baseline floor of {minimum_evidence}"
        ]
    return []


def _category_integrity_failures(category: str, bucket: dict) -> list[str]:
    entries = bucket.get("tests", [])
    passed = sum(entry.get("passed") is True for entry in entries)
    failures = _count_mismatches(
        category, bucket, {"passed": passed, "failed": len(entries) - passed}
    )
    failures.extend(
        f"{category}: invalid recorded field {field}"
        for entry in entries
        for field in _invalid_record_fields(entry)
    )
    return failures + _duplicate_result_failures(category, entries)


def _duplicate_result_failures(category: str, entries: list[dict]) -> list[str]:
    names = Counter(entry.get("name") for entry in entries)
    return [
        f"{category}: duplicate recorded result {name}"
        for name, count in names.items()
        if count > 1
    ]


def _invalid_record_fields(entry: dict) -> list[str]:
    required_types = {"name": str, "fingerprint": str, "passed": bool}
    invalid_types = [
        field
        for field, expected_type in required_types.items()
        if not isinstance(entry.get(field), expected_type)
    ]
    return invalid_types + [
        field for field in ("name", "fingerprint") if entry.get(field) == ""
    ]


def _count_mismatches(context: str, recorded: dict, expected: dict) -> list[str]:
    return [
        f"{context} {field} does not match recorded outcomes"
        for field, count in expected.items()
        if not _recorded_count_matches(recorded.get(field), count)
    ]


def _valid_recorded_count(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _recorded_count_matches(recorded, expected: int) -> bool:
    return _valid_recorded_count(recorded) and recorded == expected
