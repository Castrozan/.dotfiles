import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from run_evals_assertions import check_assertions
from run_evals_claude_cli import run_claude_cli
from run_evals_hook_test_runner import evaluate_hook_test
from run_evals_judge import build_llm_judge
from run_evals_config_loader import resolve_system_prompt_for_test
from run_evals_progress import EvaluationProgressReporter

DEFAULT_PARALLEL_WORKERS = 2


@dataclass
class TestResult:
    __test__ = False

    name: str
    passed: bool
    duration: float
    output: str
    assertions_failed: list[str]
    error: str | None = None
    category: str = "other"


def run_test(
    test: dict,
    settings: dict,
    dry_run: bool = False,
    authored_category: str = "other",
) -> TestResult:
    name = test["name"]
    model = test.get("model", settings.get("default_model", "sonnet"))
    timeout = settings.get("timeout_seconds", 120)

    if test.get("type") == "hook_test":
        hook_start_time = time.time()
        hook_failures = evaluate_hook_test(test)
        return TestResult(
            name=name,
            passed=len(hook_failures) == 0,
            duration=time.time() - hook_start_time,
            output="[hook_test]",
            assertions_failed=hook_failures,
            category=authored_category,
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
            category=authored_category,
        )

    if dry_run:
        return TestResult(
            name=name,
            passed=True,
            duration=0,
            output="[DRY RUN]",
            assertions_failed=[],
            category=authored_category,
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
            category=authored_category,
        )

    assertions = test.get("assertions", {})
    judge = (
        build_llm_judge(settings.get("judge_model", "opus"), run_claude_cli)
        if "llm_judge" in assertions
        else None
    )
    failures = check_assertions(output, assertions, judge=judge)

    return TestResult(
        name=name,
        passed=len(failures) == 0,
        duration=duration,
        output=output[:500],
        assertions_failed=failures,
        category=authored_category,
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
            return [run_test(smoke, settings, dry_run, "smoke")]
        return []

    tests_config = config.get("tests", {})
    tests_to_run = []

    for cat_name, tests in tests_config.items():
        if category and cat_name != category:
            continue

        for test in tests:
            if test_name and test["name"] != test_name:
                continue
            tests_to_run.append((test, cat_name))

    if dry_run or len(tests_to_run) <= 1:
        return [
            run_test(test, settings, dry_run, cat_name)
            for test, cat_name in tests_to_run
        ]

    max_workers = max_workers_override or settings.get(
        "parallel_workers", DEFAULT_PARALLEL_WORKERS
    )
    results_by_index = {}
    reporter = EvaluationProgressReporter(len(tests_to_run), max_workers)
    reporter.announce_start()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {
            executor.submit(run_test, test, settings, False, cat_name): index
            for index, (test, cat_name) in enumerate(tests_to_run)
        }
        for future in as_completed(future_to_index):
            result = future.result()
            results_by_index[future_to_index[future]] = result
            reporter.record(result)

    reporter.announce_finish()
    return [results_by_index[index] for index in range(len(tests_to_run))]
