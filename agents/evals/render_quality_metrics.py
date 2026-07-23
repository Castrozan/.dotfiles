#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
STATIC_EVAL_BASELINE_PATH = REPOSITORY_ROOT / "agents/evals/baseline.json"
STATIC_EVAL_SUITE_DIRECTORY = REPOSITORY_ROOT / "agents/evals/config"
END_TO_END_SCENARIO_DIRECTORY = REPOSITORY_ROOT / "agents/evals/e2e/scenarios"
INTEGRATION_SCENARIO_DIRECTORY = REPOSITORY_ROOT / "agents/evals/integration/scenarios"
CORE_RULES_PATH = REPOSITORY_ROOT / "agents/core_rules/core.md"
HOOK_EVENT_ROOT_DIRECTORY = REPOSITORY_ROOT / "agents/hooks"
DIRECTORIES_THAT_ARE_NOT_HOOK_EVENTS = frozenset(
    {"common", "lint", "__tests__", "__pycache__"}
)
RULE_BLOCK_OPENING_TAG_PATTERN = re.compile(r"^<[a-z][a-z-]*>$", re.MULTILINE)


def count_scenario_definitions(scenarioDirectory: Path) -> int:
    return len(list(scenarioDirectory.rglob("*.yaml")))


def count_static_eval_suites() -> int:
    return len(list(STATIC_EVAL_SUITE_DIRECTORY.glob("*.yaml")))


def read_static_eval_baseline() -> dict:
    baseline = json.loads(STATIC_EVAL_BASELINE_PATH.read_text())
    return {
        "totalTests": baseline["total_tests"],
        "passedTests": baseline["total_passed"],
        "passRate": baseline["pass_rate"],
        "suiteCount": count_static_eval_suites(),
        "categoryCount": len(baseline["categories"]),
        "recordedAt": baseline["generated_at"],
        "recordedCommit": baseline["git_commit"][:8],
    }


def measure_core_rules_shape() -> dict:
    coreRulesText = CORE_RULES_PATH.read_text()
    return {
        "lineCount": len(coreRulesText.splitlines()),
        "ruleBlockCount": len(RULE_BLOCK_OPENING_TAG_PATTERN.findall(coreRulesText)),
    }


def is_hook_entry_point_module(candidate: Path) -> bool:
    return candidate.suffix == ".py" and "-" in candidate.stem


def count_hook_entry_points(hookEventDirectory: Path) -> int:
    topLevelEntryPoints = [
        child
        for child in hookEventDirectory.iterdir()
        if is_hook_entry_point_module(child)
    ]
    nestedHookDirectories = [
        child
        for child in hookEventDirectory.iterdir()
        if child.is_dir()
        and child.name not in DIRECTORIES_THAT_ARE_NOT_HOOK_EVENTS
        and any(child.rglob("*.py"))
    ]
    return len(topLevelEntryPoints) + len(nestedHookDirectories)


def list_wired_hook_events() -> list[Path]:
    return sorted(
        (
            entry
            for entry in HOOK_EVENT_ROOT_DIRECTORY.iterdir()
            if entry.is_dir()
            and entry.name not in DIRECTORIES_THAT_ARE_NOT_HOOK_EVENTS
            and any(entry.rglob("*.py"))
        ),
        key=lambda entry: entry.name,
    )


def summarize_hooks() -> dict:
    wiredHookEvents = list_wired_hook_events()
    return {
        "wiredEvents": [entry.name for entry in wiredHookEvents],
        "entryPointCount": sum(
            count_hook_entry_points(entry) for entry in wiredHookEvents
        ),
    }


def read_current_repository_commit() -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(REPOSITORY_ROOT), "rev-parse", "--short=8", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def build_quality_metrics() -> dict:
    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "generatedCommit": read_current_repository_commit(),
        "staticEvals": read_static_eval_baseline(),
        "integrationScenarioCount": count_scenario_definitions(
            INTEGRATION_SCENARIO_DIRECTORY
        ),
        "endToEndScenarioCount": count_scenario_definitions(
            END_TO_END_SCENARIO_DIRECTORY
        ),
        "coreRules": measure_core_rules_shape(),
        "hooks": summarize_hooks(),
    }


def write_quality_metrics(destinationPath: Path) -> None:
    destinationPath.parent.mkdir(parents=True, exist_ok=True)
    destinationPath.write_text(json.dumps(build_quality_metrics(), indent=2) + "\n")


def main() -> None:
    if len(sys.argv) != 2:
        print(
            "usage: render_quality_metrics.py <destination-metrics-json-path>",
            file=sys.stderr,
        )
        sys.exit(2)
    destinationPath = Path(sys.argv[1])
    write_quality_metrics(destinationPath)
    print(f"wrote quality metrics to {destinationPath}")


if __name__ == "__main__":
    main()
