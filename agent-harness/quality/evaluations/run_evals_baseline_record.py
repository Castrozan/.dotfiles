import json
import subprocess
from datetime import datetime, timezone

from run_evals_baseline_policy import (
    preserved_evidence_profiles,
)
from run_evals_fingerprint import (
    evaluation_category_names,
    evaluation_fingerprints,
    humanize_recovery_fingerprints,
)
from run_evals_worktree_and_environment import REPO_ROOT

BASELINE_PATH = (
    REPO_ROOT / "agent-harness" / "quality" / "evaluations" / "baseline.json"
)


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


def merge_baseline_categories(
    existing_baseline: dict,
    replacements: dict,
    execution_profile: dict,
    token_usage: dict,
) -> dict:
    if (
        existing_baseline
        and existing_baseline.get("execution_profile") != execution_profile
    ):
        raise ValueError("existing baseline execution profile does not match")
    current_categories = evaluation_category_names()
    categories = {
        name: bucket
        for name, bucket in existing_baseline.get("categories", {}).items()
        if name in current_categories
    }
    categories.update(replacements)
    total_passed = sum(bucket["passed"] for bucket in categories.values())
    total_tests = sum(
        bucket["passed"] + bucket["failed"] for bucket in categories.values()
    )
    generated_at = (
        existing_baseline.get("generated_at") or datetime.now(timezone.utc).isoformat()
    )
    return {
        "generated_at": generated_at,
        "git_commit": get_current_git_commit(),
        "total_tests": total_tests,
        "total_passed": total_passed,
        "total_failed": total_tests - total_passed,
        "pass_rate": round(total_passed / total_tests, 4) if total_tests else 0,
        "categories": dict(sorted(categories.items())),
        "fingerprints": evaluation_fingerprints(),
        "execution_profile": execution_profile,
        "token_usage": token_usage,
        "evidence_profiles": preserved_evidence_profiles(
            existing_baseline,
            humanize_recovery_fingerprints(),
            execution_profile,
        ),
    }


def repeated_outcomes_category_bucket(
    outcomes: dict[str, list[bool]],
    fingerprints: dict[str, str],
    generated_at: str,
) -> dict:
    tests = []
    for outcome_key, samples in sorted(outcomes.items()):
        name = outcome_key.split("::", 1)[-1]
        passes = sum(samples)
        tests.append(
            {
                "name": name,
                "passed": passes * 2 >= len(samples),
                "passes": passes,
                "samples": len(samples),
                "fingerprint": fingerprints[outcome_key],
                "generated_at": generated_at,
            }
        )
    passed = sum(test["passed"] for test in tests)
    return {"passed": passed, "failed": len(tests) - passed, "tests": tests}


def merge_baseline_snapshot(
    snapshot: dict, execution_profile: dict, token_usage: dict
) -> dict:
    existing_baseline = (
        json.loads(BASELINE_PATH.read_text()) if BASELINE_PATH.exists() else {}
    )
    return merge_baseline_categories(
        existing_baseline, snapshot["categories"], execution_profile, token_usage
    )


def write_baseline(baseline: dict) -> None:
    with open(BASELINE_PATH, "w") as baseline_file:
        json.dump(baseline, baseline_file, indent=2)
    print(f"\nBaseline saved to {BASELINE_PATH}")
    print(f"  Pass rate: {baseline['pass_rate']:.1%}")
    print(f"  Tests: {baseline['total_passed']}/{baseline['total_tests']}")
    print(f"  Commit: {baseline['git_commit']}")
    if baseline.get("sampling"):
        print(f"  Epochs: {baseline['sampling']['epochs']}")
