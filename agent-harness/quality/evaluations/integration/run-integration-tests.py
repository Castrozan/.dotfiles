#!/usr/bin/env python3

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import integration_scenario_execution
from integration_models import ScenarioResult, SessionTrace
from integration_reporting import print_scenario_results
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

        return integration_scenario_execution.run_live_scenario(
            scenario,
            scenario_name,
            prompt,
            workspace_directory,
            timeout,
            model,
        )

    finally:
        shutil.rmtree(workspace_directory, ignore_errors=True)


def main():
    args = _parse_arguments()
    scenario_files = discover_scenario_files(args.scenarios_dir)
    _require_scenario_files(scenario_files, args.scenarios_dir)
    if args.list:
        _print_available_scenarios(scenario_files)
        sys.exit(0)
    scenario_files = _filter_scenario_files(scenario_files, args.scenario)
    if not args.dry_run:
        _require_claude_cli()
    results = _run_scenarios(scenario_files, args.model, args.dry_run)
    all_passed = print_scenario_results(results)
    sys.exit(0 if all_passed else 1)


def _parse_arguments():
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
    return parser.parse_args()


def _require_scenario_files(scenario_files, scenarios_directory):
    if not scenario_files:
        print("No scenario files found in", scenarios_directory)
        sys.exit(1)


def _print_available_scenarios(scenario_files):
    print("Available integration test scenarios:")
    for scenario_file in scenario_files:
        scenario = load_scenario(scenario_file)
        print(f"  {scenario['name']}: {scenario.get('description', '')}")


def _filter_scenario_files(scenario_files, scenario_name):
    if not scenario_name:
        return scenario_files
    selected_scenario_files = [
        scenario_file
        for scenario_file in scenario_files
        if load_scenario(scenario_file)["name"] == scenario_name
    ]
    if not selected_scenario_files:
        print(f"Scenario '{scenario_name}' not found")
        sys.exit(1)
    return selected_scenario_files


def _require_claude_cli():
    result = subprocess.run(["which", "claude"], capture_output=True)
    if result.returncode != 0:
        print("Error: claude CLI not found")
        sys.exit(1)


def _run_scenarios(scenario_files, model, dry_run):
    results = []
    for scenario_file in scenario_files:
        result = run_scenario(
            scenario_file,
            model=model,
            dry_run=dry_run,
        )
        results.append(result)
    return results


if __name__ == "__main__":
    main()
