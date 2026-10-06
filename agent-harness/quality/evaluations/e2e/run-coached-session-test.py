#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from e2e.coaching.coached_fixtures import SCENARIOS_DIR
from e2e.coaching.coached_reporting import print_coached_results
from e2e.coaching.coached_scenario_runner import run_coached_scenario


def main():
    parser = argparse.ArgumentParser(
        description="Run coached session tests (worker + compliance coach)",
    )
    parser.add_argument("--scenario", help="Specific scenario name")
    parser.add_argument("--model", default="opus", help="Model for worker")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--scenarios-dir", default=SCENARIOS_DIR, type=Path)
    args = parser.parse_args()

    scenario_files = sorted(
        [
            *args.scenarios_dir.glob("*.yaml"),
            *(args.scenarios_dir / "no-comments").glob("*.yaml"),
        ],
        key=lambda path: path.name,
    )

    if args.list:
        _print_available_scenarios(scenario_files)
        sys.exit(0)

    scenario_files = _filter_scenarios(scenario_files, args.scenario)

    results = []
    for sf in scenario_files:
        scenario = yaml.safe_load(sf.read_text())
        print(f"Running coached: {scenario['name']}...")
        result = run_coached_scenario(sf, model=args.model)
        results.append(result)

    print_coached_results(results)


def _print_available_scenarios(scenario_files):
    print("Available scenarios:")
    for scenario_file in scenario_files:
        scenario = yaml.safe_load(scenario_file.read_text())
        print(f"  {scenario['name']}: {scenario.get('description', '')}")


def _filter_scenarios(scenario_files, selected_scenario):
    if not selected_scenario:
        return scenario_files
    selected_files = [
        scenario_file
        for scenario_file in scenario_files
        if yaml.safe_load(scenario_file.read_text())["name"] == selected_scenario
    ]
    return selected_files


if __name__ == "__main__":
    main()
