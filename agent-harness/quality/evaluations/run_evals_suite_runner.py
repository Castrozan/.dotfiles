from concurrent.futures import ThreadPoolExecutor, as_completed

from run_evals_progress import EvaluationProgressReporter
from run_evals_test_runner import TestResult, run_test

DEFAULT_PARALLEL_WORKERS = 2


def selected_tests(config: dict, category: str | None, test_name: str | None) -> list:
    selected = []
    for category_name, tests in config.get("tests", {}).items():
        if category and category_name != category:
            continue
        for test in tests:
            if not test_name or test["name"] == test_name:
                selected.append((test, category_name))
    return selected


def run_tests(
    config: dict,
    category: str | None = None,
    test_name: str | None = None,
    dry_run: bool = False,
    smoke_only: bool = False,
    max_workers_override: int | None = None,
    instruction_ref: str | None = None,
    harness: str = "claude",
    judge_harness: str = "claude",
) -> list[TestResult]:
    settings = config.get("settings", {})
    if smoke_only:
        smoke = config.get("smoke_test")
        if not smoke:
            return []
        return [
            run_test(
                smoke,
                settings,
                dry_run,
                "smoke",
                harness=harness,
                judge_harness=judge_harness,
            )
        ]
    tests_to_run = selected_tests(config, category, test_name)
    if dry_run or len(tests_to_run) <= 1:
        return [
            run_test(
                test,
                settings,
                dry_run,
                category_name,
                instruction_ref,
                harness,
                judge_harness,
            )
            for test, category_name in tests_to_run
        ]
    max_workers = max_workers_override or settings.get(
        "parallel_workers", DEFAULT_PARALLEL_WORKERS
    )
    results_by_index = {}
    reporter = EvaluationProgressReporter(len(tests_to_run), max_workers)
    reporter.announce_start()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {
            executor.submit(
                run_test,
                test,
                settings,
                False,
                category_name,
                instruction_ref,
                harness,
                judge_harness,
            ): index
            for index, (test, category_name) in enumerate(tests_to_run)
        }
        for future in as_completed(future_to_index):
            result = future.result()
            results_by_index[future_to_index[future]] = result
            reporter.record(result)
    reporter.announce_finish()
    return [results_by_index[index] for index in range(len(tests_to_run))]
