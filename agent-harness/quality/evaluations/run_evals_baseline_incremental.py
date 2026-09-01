import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from run_evals_baseline_policy import preserved_evidence_profiles
from run_evals_baseline_record import BASELINE_PATH, get_current_git_commit
from run_evals_fingerprint import (
    evaluation_fingerprints,
    humanize_recovery_fingerprints,
)
from run_evals_impact import recorded_test_entries, test_key
from run_evals_provider_usage import merge_provider_usage, provider_usage_summary
from run_evals_test_runner import TestResult


def read_baseline(path: Path = BASELINE_PATH) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def reusable_test_entries(
    baseline: dict,
    execution_profile: dict,
    current_fingerprints: dict[str, str],
) -> dict[str, dict]:
    if baseline.get("execution_profile") != execution_profile:
        return {}
    entries = {}
    for category, bucket in baseline.get("categories", {}).items():
        for entry in bucket.get("tests", []):
            key = test_key(category, entry["name"])
            if entry.get("fingerprint") == current_fingerprints.get(key):
                entries[key] = entry
    return entries


def categories_from_entries(entries: dict[str, dict]) -> dict:
    categories = {}
    for key, entry in sorted(entries.items()):
        category = key.rsplit("::", 1)[0]
        bucket = categories.setdefault(
            category, {"passed": 0, "failed": 0, "tests": []}
        )
        bucket["tests"].append(entry)
        bucket["passed" if entry["passed"] else "failed"] += 1
    return categories


def merge_baseline_results(
    existing_baseline: dict,
    results: list[TestResult],
    execution_profile: dict,
    token_usage: dict,
    current_fingerprints: dict[str, str],
    generated_at: str,
) -> dict:
    entries = reusable_test_entries(
        existing_baseline, execution_profile, current_fingerprints
    )
    for result in results:
        key = test_key(result.category, result.name)
        entries[key] = {
            "name": result.name,
            "passed": result.passed,
            "fingerprint": current_fingerprints[key],
            "generated_at": generated_at,
        }
    categories = categories_from_entries(entries)
    total_passed = sum(bucket["passed"] for bucket in categories.values())
    total_tests = sum(
        bucket["passed"] + bucket["failed"] for bucket in categories.values()
    )
    evidence_timestamps = [
        entry["generated_at"] for entry in entries.values() if entry.get("generated_at")
    ]
    return {
        "generated_at": min(evidence_timestamps, default=generated_at),
        "git_commit": get_current_git_commit(),
        "total_tests": total_tests,
        "total_passed": total_passed,
        "total_failed": total_tests - total_passed,
        "pass_rate": round(total_passed / total_tests, 4) if total_tests else 0,
        "categories": categories,
        "fingerprints": evaluation_fingerprints(),
        "execution_profile": execution_profile,
        "token_usage": token_usage,
        "evidence_profiles": preserved_evidence_profiles(
            existing_baseline,
            humanize_recovery_fingerprints(),
            execution_profile,
        ),
    }


def write_baseline_checkpoint(
    baseline: dict, path: Path = BASELINE_PATH, announce: bool = False
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as temporary_file:
            json.dump(baseline, temporary_file, indent=2)
            temporary_file.write("\n")
            temporary_path = Path(temporary_file.name)
        temporary_path.replace(path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    if announce:
        print(f"\nBaseline saved to {path}")
        print(f"  Pass rate: {baseline['pass_rate']:.1%}")
        print(f"  Tests: {baseline['total_passed']}/{baseline['total_tests']}")
        print(f"  Commit: {baseline['git_commit']}")


class BaselineCheckpoint:
    def __init__(
        self,
        execution_profile: dict,
        current_fingerprints: dict[str, str],
        path: Path = BASELINE_PATH,
        reset_test_keys: set[str] | None = None,
    ):
        existing = read_baseline(path)
        self.path = path
        self.execution_profile = execution_profile
        self.current_fingerprints = current_fingerprints
        self.initial_usage = (
            existing.get("token_usage", {})
            if reset_test_keys != set(current_fingerprints)
            and existing.get("execution_profile") == execution_profile
            else {}
        )
        if reset_test_keys:
            entries = recorded_test_entries(existing)
            existing = {
                **existing,
                "categories": categories_from_entries(
                    {
                        key: entry
                        for key, entry in entries.items()
                        if key not in reset_test_keys
                    }
                ),
            }
        self.baseline = existing
        self.recorded_results = 0

    def record(self, result: TestResult) -> None:
        if result.error:
            return
        generated_at = datetime.now(timezone.utc).isoformat()
        token_usage = merge_provider_usage(self.initial_usage, provider_usage_summary())
        self.baseline = merge_baseline_results(
            self.baseline,
            [result],
            self.execution_profile,
            token_usage,
            self.current_fingerprints,
            generated_at,
        )
        write_baseline_checkpoint(self.baseline, self.path)
        self.recorded_results += 1

    def announce(self) -> None:
        if self.recorded_results == 0:
            print("Baseline already contains every selected current result.")
            return
        write_baseline_checkpoint(self.baseline, self.path, announce=True)
