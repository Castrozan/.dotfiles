import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

import run_evals_worktree_and_environment
from run_evals_assertions import check_assertions
from run_evals_config_loader import resolve_system_prompt_for_test
from run_evals_worktree_and_environment import build_filtered_environment

DEFAULT_PARALLEL_WORKERS = 3
TRANSIENT_RETRY_ATTEMPTS = 2
TRANSIENT_RETRY_BACKOFF_SECONDS = 3


@dataclass
class TestResult:
    name: str
    passed: bool
    duration: float
    output: str
    assertions_failed: list[str]
    error: str | None = None


def run_claude_cli(
    prompt: str,
    model: str = "sonnet",
    system_prompt: str | None = None,
    timeout: int = 120,
    no_tools: bool = False,
) -> tuple[str, bool]:
    cmd = ["claude", "-p", "--model", model, "--strict-mcp-config"]

    if no_tools:
        cmd.extend(["--tools", ""])

    if system_prompt:
        cmd.extend(["--system-prompt", system_prompt])

    cmd.append(prompt)

    last_transient_failure = ""
    for attempt in range(TRANSIENT_RETRY_ATTEMPTS + 1):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=run_evals_worktree_and_environment.EVAL_WORKING_DIRECTORY,
                env=build_filtered_environment(),
            )
            if result.returncode == 0:
                return result.stdout + result.stderr, True
            last_transient_failure = result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            last_transient_failure = f"Timeout after {timeout}s"
        except FileNotFoundError:
            return "claude CLI not found - run 'rebuild' first", False
        except Exception as e:
            return str(e), False
        if attempt < TRANSIENT_RETRY_ATTEMPTS:
            time.sleep(TRANSIENT_RETRY_BACKOFF_SECONDS * (attempt + 1))
    return last_transient_failure, False


def run_test(test: dict, settings: dict, dry_run: bool = False) -> TestResult:
    name = test["name"]
    model = test.get("model", settings.get("default_model", "sonnet"))
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
        no_tools=test.get("no_tools", False),
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
    max_workers_override: int | None = None,
) -> list[TestResult]:
    settings = config.get("settings", {})

    if smoke_only:
        smoke = config.get("smoke_test")
        if smoke:
            return [run_test(smoke, settings, dry_run)]
        return []

    tests_config = config.get("tests", {})
    tests_to_run = []

    for cat_name, tests in tests_config.items():
        if category and cat_name != category:
            continue

        for test in tests:
            if test_name and test["name"] != test_name:
                continue
            tests_to_run.append(test)

    if dry_run or len(tests_to_run) <= 1:
        return [run_test(test, settings, dry_run) for test in tests_to_run]

    max_workers = max_workers_override or settings.get(
        "parallel_workers", DEFAULT_PARALLEL_WORKERS
    )
    results_by_name = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_test_name = {
            executor.submit(run_test, test, settings, False): test["name"]
            for test in tests_to_run
        }
        for future in as_completed(future_to_test_name):
            test_name_key = future_to_test_name[future]
            results_by_name[test_name_key] = future.result()

    return [results_by_name[test["name"]] for test in tests_to_run]
