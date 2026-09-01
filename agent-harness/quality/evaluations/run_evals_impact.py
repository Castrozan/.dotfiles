import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from run_evals_baseline_thresholds import MAXIMUM_BASELINE_AGE_DAYS
from run_evals_config_loader import skill_body_from_content
from run_evals_fingerprint import instruction_wording
from run_evals_worktree_and_environment import REPO_ROOT


EXECUTION_FIELDS = frozenset({"model", "models", "max_turns"})
INSTRUCTION_LOCATION_FIELDS = frozenset({"agent", "extra_skill_paths", "skill_path"})


def test_key(category: str, test_name: str) -> str:
    return f"{category}::{test_name}"


def instruction_paths_for_test(repo_root: Path, test: dict) -> list[Path]:
    primary_path = test.get("skill_path")
    if not primary_path and test.get("agent"):
        primary_path = (
            f"agent-harness/agent-instructions/skills/{test['agent']}/SKILL.md"
        )
    path_values = [primary_path] if primary_path else []
    path_values.extend(test.get("extra_skill_paths") or [])
    return [path for value in path_values if (path := repo_root / value).is_file()]


def evaluation_test_fingerprints(
    config: dict,
    repo_root: Path = REPO_ROOT,
) -> dict[str, str]:
    fingerprints = {}
    for category, tests in config.get("tests", {}).items():
        for test in tests:
            instructions = [
                instruction_wording(
                    skill_body_from_content(path.read_text(encoding="utf-8"))
                )
                for path in instruction_paths_for_test(repo_root, test)
            ]
            payload = {
                "category": category,
                "instructions": instructions,
                "test": {
                    key: value
                    for key, value in test.items()
                    if key not in EXECUTION_FIELDS | INSTRUCTION_LOCATION_FIELDS
                },
            }
            encoded = json.dumps(
                payload, sort_keys=True, separators=(",", ":")
            ).encode()
            fingerprints[test_key(category, test["name"])] = hashlib.sha256(
                encoded
            ).hexdigest()
    return fingerprints


def recorded_test_entries(baseline: dict) -> dict[str, dict]:
    return {
        test_key(category, test["name"]): test
        for category, bucket in baseline.get("categories", {}).items()
        for test in bucket.get("tests", [])
    }


def selected_test_keys_for_filters(
    current_fingerprints: dict[str, str],
    category: str | None = None,
    test_name: str | None = None,
) -> set[str]:
    return {
        key
        for key in current_fingerprints
        if (category is None or key.startswith(f"{category}::"))
        and (test_name is None or key.rsplit("::", 1)[-1] == test_name)
    }


def affected_test_keys(
    config: dict,
    baseline: dict,
    repo_root: Path = REPO_ROOT,
    category: str | None = None,
    test_name: str | None = None,
) -> set[str]:
    current = evaluation_test_fingerprints(config, repo_root)
    selected = selected_test_keys_for_filters(current, category, test_name)
    recorded = recorded_test_entries(baseline)
    cutoff = datetime.now(timezone.utc).timestamp() - (
        MAXIMUM_BASELINE_AGE_DAYS * 24 * 60 * 60
    )
    affected = set()
    for key in selected:
        entry = recorded.get(key)
        if entry is None or entry.get("fingerprint") != current[key]:
            affected.add(key)
            continue
        try:
            generated_at = datetime.fromisoformat(entry["generated_at"])
        except (KeyError, TypeError, ValueError):
            affected.add(key)
            continue
        if generated_at.timestamp() < cutoff:
            affected.add(key)
    return affected
