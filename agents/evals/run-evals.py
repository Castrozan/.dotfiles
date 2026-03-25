#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class TestResult:
    name: str
    passed: bool
    duration: float
    output: str
    assertions_failed: list[str]
    error: str | None = None


def load_skill_body_from_path(skill_path: Path) -> str | None:
    if not skill_path.exists():
        return None
    content = skill_path.read_text()
    parts = content.split("---", 2)
    if len(parts) >= 3:
        return parts[2].strip()
    return content.strip()


def resolve_system_prompt_for_test(test: dict) -> str | None:
    if "system_prompt" in test:
        return test["system_prompt"]

    skill_path_value = test.get("skill_path")
    if not skill_path_value:
        agent_name = test.get("agent")
        if agent_name:
            skill_path_value = f"agents/skills/{agent_name}/SKILL.md"
        else:
            return None

    resolved_path = REPO_ROOT / skill_path_value
    return load_skill_body_from_path(resolved_path)


def discover_skill_adjacent_eval_files(repo_root: Path) -> dict[str, list[dict]]:
    discovered_tests = {}
    for yaml_file in sorted(repo_root.glob("agents/skills/*/evals/*.yaml")):
        if yaml_file.name == "settings.yaml":
            continue
        skill_name = yaml_file.parent.parent.name
        category_name = f"skills/{skill_name}/{yaml_file.stem}"
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
            if data and "tests" in data:
                discovered_tests[category_name] = data["tests"]
    return discovered_tests


def build_filtered_environment() -> dict[str, str]:
    filtered_env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    return filtered_env


def load_config(config_path: Path) -> dict:
    if config_path.is_dir():
        return load_config_from_dir(config_path)
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_config_from_dir(config_dir: Path) -> dict:
    config = {"settings": {}, "tests": {}, "smoke_test": None}

    settings_file = config_dir / "settings.yaml"
    if settings_file.exists():
        with open(settings_file) as f:
            data = yaml.safe_load(f)
            config["settings"] = data.get("settings", {})
            if "smoke_test" in data:
                config["smoke_test"] = data["smoke_test"]

    for yaml_file in sorted(config_dir.glob("*.yaml")):
        if yaml_file.name == "settings.yaml":
            continue
        category_name = yaml_file.stem
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
            if data and "tests" in data:
                config["tests"][category_name] = data["tests"]

    skill_adjacent_tests = discover_skill_adjacent_eval_files(REPO_ROOT)
    config["tests"].update(skill_adjacent_tests)

    return config


def check_assertions(output: str, assertions: dict) -> list[str]:
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
        found = any(
            exp.lower() in output.lower() for exp in assertions["output_contains_any"]
        )
        if not found:
            failures.append(
                f"Expected one of {assertions['output_contains_any']} in output"
            )

    return failures


def run_claude_cli(
    prompt: str,
    model: str = "haiku",
    system_prompt: str | None = None,
    timeout: int = 120,
) -> tuple[str, bool]:
    cmd = ["claude", "-p", "--model", model]

    if system_prompt:
        cmd.extend(["--system-prompt", system_prompt])

    cmd.append(prompt)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=REPO_ROOT,
            env=build_filtered_environment(),
        )
        return result.stdout + result.stderr, result.returncode == 0
    except subprocess.TimeoutExpired:
        return f"Timeout after {timeout}s", False
    except FileNotFoundError:
        return "claude CLI not found - run 'rebuild' first", False
    except Exception as e:
        return str(e), False


def run_test(test: dict, settings: dict, dry_run: bool = False) -> TestResult:
    name = test["name"]
    model = test.get("model", settings.get("default_model", "haiku"))
    timeout = settings.get("timeout_seconds", 120)

    if test.get("type") == "hook_test":
        return TestResult(
            name=name,
            passed=True,
            duration=0,
            output="[SKIP] Hook tests require interactive session",
            assertions_failed=[],
        )

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

    resolved_system_prompt = resolve_system_prompt_for_test(test)

    output, success = run_claude_cli(
        prompt=prompt,
        model=model,
        system_prompt=resolved_system_prompt,
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
        output=output[:500],
        assertions_failed=failures,
    )


def run_tests(
    config: dict,
    category: str | None = None,
    test_name: str | None = None,
    dry_run: bool = False,
    smoke_only: bool = False,
) -> list[TestResult]:
    results = []
    settings = config.get("settings", {})

    if smoke_only:
        smoke = config.get("smoke_test")
        if smoke:
            result = run_test(smoke, settings, dry_run)
            results.append(result)
        return results

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
    print("\n" + "=" * 60)
    print("AGENT EVALUATION RESULTS (Claude Max/CLI)")
    print("=" * 60 + "\n")

    passed = 0
    failed = 0
    total_duration = 0.0

    for result in results:
        total_duration += result.duration
        status = "\u2713" if result.passed else "\u2717"
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
    print("Available test categories:")
    for cat_name, tests in config.get("tests", {}).items():
        print(f"  {cat_name} ({len(tests)} tests)")
        for test in tests:
            print(f"    - {test['name']}")
    if config.get("smoke_test"):
        print("  smoke_test (1 test)")
        print(f"    - {config['smoke_test']['name']}")


def main():
    parser = argparse.ArgumentParser(
        description="Run agent evaluations (Claude Max/CLI)"
    )
    parser.add_argument("--smoke", action="store_true", help="Run smoke test only")
    parser.add_argument("--category", help="Run tests in specific category")
    parser.add_argument("--test", help="Run specific test by name")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run")
    parser.add_argument(
        "--list", action="store_true", help="List available categories and tests"
    )
    parser.add_argument("--config", default=Path(__file__).parent / "config")
    args = parser.parse_args()

    config = load_config(Path(args.config))

    if args.list:
        list_categories(config)
        sys.exit(0)

    if not args.dry_run:
        result = subprocess.run(["which", "claude"], capture_output=True)
        if result.returncode != 0:
            print("Error: claude CLI not found")
            print("Run 'rebuild' to install Claude Code")
            sys.exit(1)

    print("Running agent evaluations (Claude Max - no API cost)...")
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
