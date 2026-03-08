#!/usr/bin/env python3
"""
Agent Evaluation Runner (Claude Max/CLI version)

Runs tests defined in config/ directory using Claude Code CLI.
Uses your Claude Max subscription - no API costs!

Usage:
    ./run-evals.py                    # Run all tests
    ./run-evals.py --smoke            # Run smoke test only
    ./run-evals.py --category core_rules
    ./run-evals.py --test delegates_to_skill
    ./run-evals.py --dry-run          # Show what would run
    ./run-evals.py --list             # List available categories
"""

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class TestResult:
    name: str
    passed: bool
    duration: float
    output: str
    assertions_failed: list[str]
    error: str | None = None


def load_config(config_path: Path) -> dict:
    """Load config from directory or single file."""
    if config_path.is_dir():
        return load_config_from_dir(config_path)
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_config_from_dir(config_dir: Path) -> dict:
    """Load config from multiple YAML files in a directory."""
    config = {"settings": {}, "tests": {}, "smoke_test": None}

    # Load settings first
    settings_file = config_dir / "settings.yaml"
    if settings_file.exists():
        with open(settings_file) as f:
            data = yaml.safe_load(f)
            config["settings"] = data.get("settings", {})
            if "smoke_test" in data:
                config["smoke_test"] = data["smoke_test"]

    # Load category files (any yaml file except settings.yaml)
    for yaml_file in sorted(config_dir.glob("*.yaml")):
        if yaml_file.name == "settings.yaml":
            continue

        category_name = yaml_file.stem  # e.g., "core_rules" from "core_rules.yaml"
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
            if data and "tests" in data:
                config["tests"][category_name] = data["tests"]

    return config


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


def run_claude_cli(
    prompt: str,
    model: str = "haiku",
    system_prompt: str | None = None,
    agent: str | None = None,
    timeout: int = 120,
) -> tuple[str, bool]:
    """Run claude CLI with --print flag and return output."""
    cmd = ["claude", "--print", "--model", model]

    if system_prompt:
        cmd.extend(["--system-prompt", system_prompt])

    if agent:
        # Load agent from file
        agent_path = Path(__file__).parent.parent.parent / "agents" / "skills" / agent / "SKILL.md"
        if agent_path.exists():
            content = agent_path.read_text()
            parts = content.split("---", 2)
            if len(parts) >= 3:
                agent_instructions = parts[2].strip()
                cmd.extend(["--system-prompt", agent_instructions])

    cmd.append(prompt)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path.home() / ".dotfiles",  # Run in dotfiles context
        )
        return result.stdout + result.stderr, result.returncode == 0
    except subprocess.TimeoutExpired:
        return f"Timeout after {timeout}s", False
    except FileNotFoundError:
        return "claude CLI not found - run 'rebuild' first", False
    except Exception as e:
        return str(e), False


def run_test(test: dict, settings: dict, dry_run: bool = False) -> TestResult:
    """Run a single test using Claude CLI."""
    name = test["name"]
    model = test.get("model", settings.get("default_model", "haiku"))
    timeout = settings.get("timeout_seconds", 120)

    # Skip hook tests (need special handling)
    if test.get("type") == "hook_test":
        return TestResult(
            name=name,
            passed=True,
            duration=0,
            output="[SKIP] Hook tests require interactive session",
            assertions_failed=[],
        )

    # Get prompt (required for non-hook tests)
    prompt = test.get("prompt")
    if not prompt:
        return TestResult(
            name=name,
            passed=False,
            duration=0,
            output="",
            assertions_failed=[],
            error="Test missing 'prompt' field",
        )

    if dry_run:
        return TestResult(
            name=name,
            passed=True,
            duration=0,
            output="[DRY RUN]",
            assertions_failed=[],
        )

    start_time = time.time()

    # Get agent if specified
    agent = test.get("agent")

    output, success = run_claude_cli(
        prompt=prompt,
        model=model,
        agent=agent,
        timeout=timeout,
    )

    duration = time.time() - start_time

    if not success and "not found" in output.lower():
        return TestResult(
            name=name,
            passed=False,
            duration=duration,
            output=output[:500],
            assertions_failed=[],
            error=output,
        )

    failures = check_assertions(output, test.get("assertions", {}))

    return TestResult(
        name=name,
        passed=len(failures) == 0,
        duration=duration,
        output=output[:500],  # Truncate for reporting
        assertions_failed=failures,
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

    # Smoke test
    if smoke_only:
        smoke = config.get("smoke_test")
        if smoke:
            result = run_test(smoke, settings, dry_run)
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

            result = run_test(test, settings, dry_run)
            results.append(result)

    return results


def print_results(results: list[TestResult]) -> bool:
    """Print results and return True if all passed."""
    print("\n" + "=" * 60)
    print("AGENT EVALUATION RESULTS (Claude Max/CLI)")
    print("=" * 60 + "\n")

    passed = 0
    failed = 0
    total_duration = 0.0

    for result in results:
        total_duration += result.duration
        status = "✓" if result.passed else "✗"
        color = "\033[32m" if result.passed else "\033[31m"
        reset = "\033[0m"

        print(f"{color}{status}{reset} {result.name} ({result.duration:.1f}s)")

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
    print(f"Total time: {total_duration:.1f}s")
    print("-" * 60 + "\n")

    return failed == 0


def list_categories(config: dict) -> None:
    """List available test categories."""
    print("Available test categories:")
    for cat_name, tests in config.get("tests", {}).items():
        print(f"  {cat_name} ({len(tests)} tests)")
        for test in tests:
            print(f"    - {test['name']}")
    if config.get("smoke_test"):
        print("  smoke_test (1 test)")
        print(f"    - {config['smoke_test']['name']}")


def main():
    parser = argparse.ArgumentParser(description="Run agent evaluations (Claude Max/CLI)")
    parser.add_argument("--smoke", action="store_true", help="Run smoke test only")
    parser.add_argument("--category", help="Run tests in specific category")
    parser.add_argument("--test", help="Run specific test by name")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run")
    parser.add_argument("--list", action="store_true", help="List available categories and tests")
    parser.add_argument("--config", default=Path(__file__).parent / "config")
    args = parser.parse_args()

    config = load_config(Path(args.config))

    if args.list:
        list_categories(config)
        sys.exit(0)

    # Check for claude CLI
    if not args.dry_run:
        result = subprocess.run(["which", "claude"], capture_output=True)
        if result.returncode != 0:
            print("Error: claude CLI not found")
            print("Run 'rebuild' to install Claude Code")
            sys.exit(1)

    print("🧪 Running agent evaluations (Claude Max - no API cost)...")
    if args.dry_run:
        print("   (dry run - no claude calls)")

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
