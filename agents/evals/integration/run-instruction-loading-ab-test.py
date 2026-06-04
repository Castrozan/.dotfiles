#!/usr/bin/env python3

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ab_test_claude_session import (
    run_claude_session_with_system_prompt,
    run_claude_session_without_system_prompt,
)
from ab_test_metrics import measure_instruction_following
from ab_test_models import AbTestResult
from ab_test_reporting import print_ab_test_results
from ab_test_scenarios import UNPROMPTED_SCENARIOS, load_core_instructions_body
from ab_test_workspace_setup import CONFIGURATION_SETUP_FUNCTIONS


def run_ab_test_for_scenario(
    scenario: dict,
    configurations: list[str],
    model: str = "haiku",
) -> list[AbTestResult]:
    results = []

    for configuration_name in configurations:
        workspace_directory = Path(
            tempfile.mkdtemp(prefix=(f"ab-{configuration_name}-{scenario['name']}-"))
        )

        try:
            setup_function = CONFIGURATION_SETUP_FUNCTIONS[configuration_name]
            setup_function(workspace_directory, scenario["files"])

            if configuration_name == "system-prompt":
                trace = run_claude_session_with_system_prompt(
                    prompt=scenario["prompt"],
                    workspace_directory=workspace_directory,
                    system_prompt=load_core_instructions_body(),
                    model=model,
                )
            else:
                trace = run_claude_session_without_system_prompt(
                    prompt=scenario["prompt"],
                    workspace_directory=workspace_directory,
                    model=model,
                )

            metrics = measure_instruction_following(trace)

            results.append(
                AbTestResult(
                    configuration_name=configuration_name,
                    scenario_name=scenario["name"],
                    metrics=metrics,
                    trace=trace,
                    duration_seconds=trace.duration_seconds,
                )
            )

        finally:
            shutil.rmtree(workspace_directory, ignore_errors=True)

    return results


def main():
    parser = argparse.ArgumentParser(
        description=(
            "A/B test: does CLAUDE.md @ reference vs "
            "inline content affect instruction following?"
        )
    )
    parser.add_argument(
        "--model",
        default="haiku",
        help="Model to use (default: haiku)",
    )
    parser.add_argument(
        "--configurations",
        nargs="+",
        default=[
            "reference",
            "inline",
            "system-prompt",
            "no-instructions",
        ],
        help="Configurations to test",
    )
    parser.add_argument(
        "--scenario",
        help="Run specific scenario only",
    )
    args = parser.parse_args()

    result = subprocess.run(["which", "claude"], capture_output=True)
    if result.returncode != 0:
        print("Error: claude CLI not found")
        sys.exit(1)

    scenarios_to_run = UNPROMPTED_SCENARIOS
    if args.scenario:
        scenarios_to_run = [
            scenario
            for scenario in UNPROMPTED_SCENARIOS
            if scenario["name"] == args.scenario
        ]
        if not scenarios_to_run:
            print(f"Scenario '{args.scenario}' not found")
            sys.exit(1)

    all_results = []
    for scenario in scenarios_to_run:
        print(f"Running: {scenario['name']}...")
        results = run_ab_test_for_scenario(
            scenario,
            args.configurations,
            model=args.model,
        )
        all_results.extend(results)

    print_ab_test_results(all_results, args.configurations)


if __name__ == "__main__":
    main()
