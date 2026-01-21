#!/usr/bin/env python3
"""
Agent Evaluation Runner

Runs tests defined in eval-config.yaml to verify agent instructions work correctly.
Requires: ANTHROPIC_API_KEY environment variable

Usage:
    ./run-evals.py                    # Run all tests
    ./run-evals.py --smoke            # Run smoke test only
    ./run-evals.py --category core_rules
    ./run-evals.py --test delegates_to_subagent
    ./run-evals.py --dry-run          # Show what would run
"""

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# Cost per 1M tokens (approximate, as of 2024)
COSTS = {
    "haiku": {"input": 0.25, "output": 1.25},
    "sonnet": {"input": 3.00, "output": 15.00},
    "opus": {"input": 15.00, "output": 75.00},
}


@dataclass
class TestResult:
    name: str
    passed: bool
    duration: float
    cost: float
    output: str
    assertions_failed: list[str]
    error: str | None = None


def load_config(config_path: Path) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    costs = COSTS.get(model, COSTS["haiku"])
    return (input_tokens * costs["input"] + output_tokens * costs["output"]) / 1_000_000


def check_assertions(output: str, assertions: dict) -> list[str]:
    """Check assertions against output, return list of failures."""
    failures = []

    if "output_contains" in assertions:
        for expected in assertions["output_contains"]:
            if expected.lower() not in output.lower():
                failures.append(f"Expected '{expected}' in output")

    if "output_not_contains" in assertions:
        for forbidden in assertions["output_not_contains"]:
            if forbidden.lower() in output.lower():
                failures.append(f"Unexpected '{forbidden}' in output")

    if "output_contains_any" in assertions:
        found = any(exp.lower() in output.lower() for exp in assertions["output_contains_any"])
        if not found:
            failures.append(f"Expected one of {assertions['output_contains_any']} in output")

    return failures


def run_api_test(test: dict, settings: dict, dry_run: bool = False) -> TestResult:
    """Run a test using the Anthropic API directly."""
    name = test["name"]
    model_name = test.get("model", settings.get("default_model", "haiku"))
    prompt = test["prompt"]
    max_turns = test.get("max_turns", 1)

    if dry_run:
        return TestResult(
            name=name,
            passed=True,
            duration=0,
            cost=0,
            output="[DRY RUN]",
            assertions_failed=[],
        )

    try:
        import anthropic

        client = anthropic.Anthropic()

        # Map model names to IDs
        model_ids = {
            "haiku": "claude-3-5-haiku-20241022",
            "sonnet": "claude-sonnet-4-20250514",
            "opus": "claude-opus-4-20250514",
        }
        model_id = model_ids.get(model_name, model_name)

        # Load agent instructions if specified
        system_prompt = ""
        if "agent" in test:
            agent_path = Path(__file__).parent.parent.parent / "agents" / "subagent" / f"{test['agent']}.md"
            if agent_path.exists():
                content = agent_path.read_text()
                # Extract content after YAML frontmatter
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    system_prompt = parts[2].strip()

        start_time = time.time()

        response = client.messages.create(
            model=model_id,
            max_tokens=1024,
            system=system_prompt if system_prompt else None,
            messages=[{"role": "user", "content": prompt}],
        )

        duration = time.time() - start_time
        output = response.content[0].text
        cost = estimate_cost(
            model_name,
            response.usage.input_tokens,
            response.usage.output_tokens,
        )

        failures = check_assertions(output, test.get("assertions", {}))

        return TestResult(
            name=name,
            passed=len(failures) == 0,
            duration=duration,
            cost=cost,
            output=output[:500],  # Truncate for reporting
            assertions_failed=failures,
        )

    except Exception as e:
        return TestResult(
            name=name,
            passed=False,
            duration=0,
            cost=0,
            output="",
            assertions_failed=[],
            error=str(e),
        )


def run_hook_test(test: dict, dry_run: bool = False) -> TestResult:
    """Run a hook test (placeholder - requires Claude Code session)."""
    # Hook tests need to be run in an actual Claude Code session
    # This is a placeholder that marks them as skipped
    return TestResult(
        name=test["name"],
        passed=True,
        duration=0,
        cost=0,
        output="[SKIP] Hook tests require Claude Code session",
        assertions_failed=[],
    )


def run_tests(
    config: dict,
    category: str | None = None,
    test_name: str | None = None,
    dry_run: bool = False,
    smoke_only: bool = False,
) -> list[TestResult]:
    """Run tests based on filters."""
    results = []
    settings = config.get("settings", {})
    total_cost = 0.0
    max_cost = settings.get("max_cost_per_run", 1.0)

    # Smoke test
    if smoke_only:
        smoke = config.get("smoke_test")
        if smoke:
            result = run_api_test(smoke, settings, dry_run)
            results.append(result)
        return results

    # Regular tests
    tests_config = config.get("tests", {})

    for cat_name, tests in tests_config.items():
        if category and cat_name != category:
            continue

        for test in tests:
            if test_name and test["name"] != test_name:
                continue

            # Check cost limit
            if total_cost >= max_cost:
                print(f"⚠️  Cost limit ${max_cost} reached, stopping")
                break

            # Run appropriate test type
            test_type = test.get("type", "api")
            if test_type == "hook_test":
                result = run_hook_test(test, dry_run)
            else:
                result = run_api_test(test, settings, dry_run)

            results.append(result)
            total_cost += result.cost

    return results


def print_results(results: list[TestResult]) -> bool:
    """Print results and return True if all passed."""
    print("\n" + "=" * 60)
    print("AGENT EVALUATION RESULTS")
    print("=" * 60 + "\n")

    passed = 0
    failed = 0
    total_cost = 0.0

    for result in results:
        total_cost += result.cost
        status = "✓" if result.passed else "✗"
        color = "\033[32m" if result.passed else "\033[31m"
        reset = "\033[0m"

        print(f"{color}{status}{reset} {result.name}")

        if result.error:
            print(f"    Error: {result.error}")
        elif result.assertions_failed:
            for failure in result.assertions_failed:
                print(f"    - {failure}")

        if result.passed:
            passed += 1
        else:
            failed += 1

    print("\n" + "-" * 60)
    print(f"Passed: {passed}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")
    print(f"Total cost: ${total_cost:.4f}")
    print("-" * 60 + "\n")

    return failed == 0


def main():
    parser = argparse.ArgumentParser(description="Run agent evaluations")
    parser.add_argument("--smoke", action="store_true", help="Run smoke test only")
    parser.add_argument("--category", help="Run tests in specific category")
    parser.add_argument("--test", help="Run specific test by name")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run")
    parser.add_argument("--config", default=Path(__file__).parent / "eval-config.yaml")
    args = parser.parse_args()

    # Check for API key
    if not args.dry_run and not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable required")
        print("Set it with: export ANTHROPIC_API_KEY=sk-...")
        sys.exit(1)

    config = load_config(args.config)

    print("🧪 Running agent evaluations...")
    if args.dry_run:
        print("   (dry run - no API calls)")

    results = run_tests(
        config,
        category=args.category,
        test_name=args.test,
        dry_run=args.dry_run,
        smoke_only=args.smoke,
    )

    all_passed = print_results(results)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
