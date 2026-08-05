#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

import yaml

from coached_fixtures import SCENARIOS_DIR
from coached_reporting import print_coached_results
from coached_scenario_runner import run_coached_scenario


def main():
    parser = argparse.ArgumentParser(
        description="Run coached session tests (worker + compliance coach)",
    )
    parser.add_argument("--scenario", help="Specific scenario name")
    parser.add_argument("--model", default="opus", help="Model for worker")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--scenarios-dir", default=SCENARIOS_DIR, type=Path)
    args = parser.parse_args()

    scenario_files = sorted(args.scenarios_dir.glob("*.yaml"))

    if args.list:
        print("Available scenarios:")
        for sf in scenario_files:
            s = yaml.safe_load(sf.read_text())
            print(f"  {s['name']}: {s.get('description', '')}")
        sys.exit(0)

    if args.scenario:
        scenario_files = [
            sf
            for sf in scenario_files
            if yaml.safe_load(sf.read_text())["name"] == args.scenario
        ]

    results = []
    for sf in scenario_files:
        scenario = yaml.safe_load(sf.read_text())
        print(f"Running coached: {scenario['name']}...")
        result = run_coached_scenario(sf, model=args.model)
        results.append(result)

    print_coached_results(results)


if __name__ == "__main__":
    main()
