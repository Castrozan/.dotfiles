from datetime import datetime, timezone
from pathlib import Path

from run_evals_baseline_policy import preserved_evidence_profiles
from run_evals_baseline_record import BASELINE_PATH, get_current_git_commit
from run_evals_baseline_store import read_baseline, write_baseline_checkpoint
from run_evals_execution_profile import execution_profile_identifier
from run_evals_fingerprint import (
    evaluation_fingerprints,
)
from run_evals_impact import recorded_test_entries, test_key
from run_evals_provider_usage import merge_provider_usage, provider_usage_summary
from run_evals_test_runner import TestResult


def retained_test_entries(
    baseline: dict,
    current_fingerprints: dict[str, str],
) -> dict[str, dict]:
    entries = {}
    for category, bucket in baseline.get("categories", {}).items():
        for entry in bucket.get("tests", []):
            key = test_key(category, entry["name"])
            if key in current_fingerprints:
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
    recorded_keys = set(recorded_test_entries(existing_baseline))
    obsolete_test_count = len(recorded_keys - set(current_fingerprints))
    entries = retained_test_entries(existing_baseline, current_fingerprints)
    execution_profile_id = execution_profile_identifier(execution_profile)
    for result in results:
        key = test_key(result.category, result.name)
        entries[key] = {
            "name": result.name,
            "passed": result.passed,
            "fingerprint": current_fingerprints[key],
            "generated_at": generated_at,
            "execution_profile_id": execution_profile_id,
            "run_source": {
                "kind": "checkpoint",
                "git_commit": get_current_git_commit(),
            },
        }
    categories = categories_from_entries(entries)
    total_passed = sum(bucket["passed"] for bucket in categories.values())
    total_tests = sum(
        bucket["passed"] + bucket["failed"] for bucket in categories.values()
    )
    evidence_timestamps = [
        entry["generated_at"] for entry in entries.values() if entry.get("generated_at")
    ]
    current_evidence_count = sum(
        entry.get("fingerprint") == current_fingerprints[key]
        for key, entry in entries.items()
    )
    prior_evidence_floor = min(
        max(
            0,
            existing_baseline.get("minimum_current_evidence", 0) - obsolete_test_count,
        ),
        len(current_fingerprints),
    )
    return {
        "generated_at": generated_at,
        "oldest_evidence_at": min(evidence_timestamps, default=generated_at),
        "git_commit": get_current_git_commit(),
        "total_tests": total_tests,
        "total_passed": total_passed,
        "total_failed": total_tests - total_passed,
        "pass_rate": round(total_passed / total_tests, 4) if total_tests else 0,
        "minimum_current_evidence": max(prior_evidence_floor, current_evidence_count),
        "categories": categories,
        "fingerprints": evaluation_fingerprints(),
        "execution_profile": execution_profile,
        "execution_profiles": {
            **existing_baseline.get("execution_profiles", {}),
            execution_profile_id: execution_profile,
        },
        "token_usage": token_usage,
        "evidence_profiles": preserved_evidence_profiles(existing_baseline),
    }


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
        self.prepared_baseline = bool(
            set(recorded_test_entries(existing)) - set(current_fingerprints)
            or existing.get("execution_profile") != execution_profile
        )
        if self.prepared_baseline:
            existing = merge_baseline_results(
                existing,
                [],
                execution_profile,
                self.initial_usage,
                current_fingerprints,
                datetime.now(timezone.utc).isoformat(),
            )
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
            if self.prepared_baseline:
                write_baseline_checkpoint(self.baseline, self.path, announce=True)
                return
            print("Baseline already contains every selected current result.")
            return
        write_baseline_checkpoint(self.baseline, self.path, announce=True)
