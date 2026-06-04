#!/usr/bin/env python3

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from integration_assertions_output import run_assertions
from integration_models import ScenarioResult, SessionTrace
from integration_reporting import print_scenario_results
from integration_scoring import calculate_experience_score
from integration_session import run_claude_session
from integration_workspace import (
    SCENARIOS_DIR,
    discover_scenario_files,
    load_scenario,
    sanitize_scenario_name_for_tempdir,
    setup_scenario_workspace,
)


def run_scenario(
    scenario_path: Path,
    model: str = "sonnet",
    dry_run: bool = False,
) -> ScenarioResult:
    scenario = load_scenario(scenario_path)
    scenario_name = scenario["name"]

    if dry_run:
        return ScenarioResult(
            scenario_name=scenario_name,
            passed=True,
            assertion_results=[],
            trace=SessionTrace(),
            workspace_directory=None,
            duration_seconds=0,
        )

    sanitized_name = sanitize_scenario_name_for_tempdir(scenario_name)
    workspace_directory = Path(
        tempfile.mkdtemp(prefix=f"claude-eval-{sanitized_name}-")
    )

    try:
        setup_scenario_workspace(scenario, workspace_directory)

        timeout = scenario.get("timeout", 180)

        prompt = scenario.get("prompt")
        if not prompt:
            return ScenarioResult(
                scenario_name=scenario_name,
                passed=False,
                assertion_results=[],
                trace=SessionTrace(),
                workspace_directory=workspace_directory,
                duration_seconds=0,
                error="Scenario missing 'prompt' field",
            )

        trace = run_claude_session(
            prompt=prompt,
            workspace_directory=workspace_directory,
            timeout_seconds=timeout,
            model=model,
        )

        if trace.exit_code == 124:
            return ScenarioResult(
                scenario_name=scenario_name,
                passed=False,
                assertion_results=[],
                trace=trace,
                workspace_directory=workspace_directory,
                duration_seconds=trace.duration_seconds,
                error=f"Session timed out after {timeout}s",
            )

        assertion_results = run_assertions(
            trace,
            scenario.get("assertions", {}),
            workspace_directory=workspace_directory,
        )
        all_passed = all(
            assertion_result.passed for assertion_result in assertion_results
        )

        experience_score = calculate_experience_score(trace, assertion_results)

        return ScenarioResult(
            scenario_name=scenario_name,
            passed=all_passed,
            assertion_results=assertion_results,
            trace=trace,
            workspace_directory=workspace_directory,
            duration_seconds=trace.duration_seconds,
            experience_score=experience_score,
        )

    finally:
        shutil.rmtree(workspace_directory, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(
        description=("Run Claude Code integration tests with real sessions")
    )
    parser.add_argument(
        "--scenario",
        help="Run a specific scenario by name",
    )
    parser.add_argument(
        "--model",
        default="sonnet",
        help="Model to use for sessions (default: sonnet)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List scenarios without running them",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available scenarios",
    )
    parser.add_argument(
        "--scenarios-dir",
        default=SCENARIOS_DIR,
        type=Path,
        help="Directory containing scenario YAML files",
    )
    args = parser.parse_args()

    scenario_files = discover_scenario_files(args.scenarios_dir)

    if not scenario_files:
        print("No scenario files found in", args.scenarios_dir)
        sys.exit(1)

    if args.list:
        print("Available integration test scenarios:")
        for scenario_file in scenario_files:
            scenario = load_scenario(scenario_file)
            print(f"  {scenario['name']}: {scenario.get('description', '')}")
        sys.exit(0)

    if args.scenario:
        scenario_files = [
            scenario_file
            for scenario_file in scenario_files
            if load_scenario(scenario_file)["name"] == args.scenario
        ]
        if not scenario_files:
            print(f"Scenario '{args.scenario}' not found")
            sys.exit(1)

    if not args.dry_run:
        result = subprocess.run(["which", "claude"], capture_output=True)
        if result.returncode != 0:
            print("Error: claude CLI not found")
            sys.exit(1)

    results = []
    for scenario_file in scenario_files:
        result = run_scenario(
            scenario_file,
            model=args.model,
            dry_run=args.dry_run,
        )
        results.append(result)

    all_passed = print_scenario_results(results)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
