#!/usr/bin/env python3

import argparse
import subprocess
import sys
from pathlib import Path

from e2e_reporting import print_e2e_results, print_multi_run_pass_rate_summary
from e2e_scenario_runner import run_e2e_scenario
from e2e_workspace import SCENARIOS_DIR, discover_scenario_files, load_scenario


def main():
    parser = argparse.ArgumentParser(
        description=("E2E herdr-based Claude Code integration tests")
    )
    parser.add_argument("--scenario", help="Run specific scenario by name")
    parser.add_argument("--model", default="sonnet", help="Model (default: sonnet)")
    parser.add_argument("--dry-run", action="store_true", help="List without running")
    parser.add_argument("--list", action="store_true", help="List scenarios")
    parser.add_argument(
        "--debug-capture",
        action="store_true",
        help="Save raw terminal output for parser calibration",
    )
    parser.add_argument(
        "--claude-ab-mode",
        default="inline",
        choices=["reference", "inline", "global-only"],
        help="Instructions loading: inline, reference, or global-only",
    )
    parser.add_argument(
        "--scenarios-dir",
        default=SCENARIOS_DIR,
        type=Path,
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Run scenarios in parallel (each in its own herdr tab)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help=(
            "Execute each scenario N independent times for stochasticity stats. "
            "Each run is an independent herdr tab; parallel cap is --workers "
            "(total concurrent herdr tabs = min(workers, scenarios * runs))."
        ),
    )
    args = parser.parse_args()

    if args.runs < 1:
        print("Error: --runs must be >= 1")
        sys.exit(1)

    scenario_files = discover_scenario_files(args.scenarios_dir)

    if not scenario_files:
        print("No scenarios found in", args.scenarios_dir)
        sys.exit(1)

    if args.list:
        print("Available E2E scenarios:")
        for sf in scenario_files:
            s = load_scenario(sf)
            print(f"  {s['name']}: {s.get('description', '')}")
        sys.exit(0)

    if args.scenario:
        scenario_files = [
            sf for sf in scenario_files if load_scenario(sf)["name"] == args.scenario
        ]
        if not scenario_files:
            print(f"Scenario '{args.scenario}' not found")
            sys.exit(1)

    if not args.dry_run:
        for tool in ["claude", "herdr"]:
            if subprocess.run(["which", tool], capture_output=True).returncode != 0:
                print(f"Error: {tool} not found")
                sys.exit(1)

    def run_one_scenario_file(scenario_file):
        scenario = load_scenario(scenario_file)
        print(f"Running: {scenario['name']}...", flush=True)
        return run_e2e_scenario(
            scenario_file,
            model=args.model,
            dry_run=args.dry_run,
            debug_capture=args.debug_capture,
            claude_ab_mode=args.claude_ab_mode,
        )

    execution_units = list(scenario_files) * args.runs

    results = []
    if args.workers <= 1:
        for sf in execution_units:
            results.append(run_one_scenario_file(sf))
    else:
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            for result in executor.map(run_one_scenario_file, execution_units):
                results.append(result)

    all_passed = print_e2e_results(results)

    if args.runs > 1:
        print_multi_run_pass_rate_summary(results, args.runs)
        total_runs = len(results)
        total_passed = sum(1 for r in results if r.passed)
        sys.exit(0 if total_passed == total_runs else 1)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
