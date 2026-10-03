from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

from reporting.run_evals_progress import EvaluationProgressReporter
from runner.execution.run_evals_test_runner import TestResult, run_test

DEFAULT_PARALLEL_WORKERS = 2


def selected_tests(
    config: dict,
    category: str | None,
    test_name: str | None,
    selected_test_keys: set[str] | None = None,
) -> list:
    selected = []
    for category_name, tests in config.get("tests", {}).items():
        if not _matches_category(category, category_name):
            continue
        for test in tests:
            key = f"{category_name}::{test['name']}"
            if _matches_test_selection(test, key, test_name, selected_test_keys):
                selected.append((test, category_name))
    return selected


def _matches_category(category: str | None, category_name: str) -> bool:
    return not category or category_name == category


def _matches_test_selection(
    test: dict, key: str, test_name: str | None, selected_test_keys: set[str] | None
) -> bool:
    if test_name and test["name"] != test_name:
        return False
    if selected_test_keys is not None and key not in selected_test_keys:
        return False
    return True


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
    selected_test_keys: set[str] | None = None,
    on_result=None,
) -> list[TestResult]:
    settings = config.get("settings", {})
    if smoke_only:
        return _run_smoke_test(
            config, settings, dry_run, harness, judge_harness, on_result
        )
    tests_to_run = selected_tests(
        config, category, test_name, selected_test_keys=selected_test_keys
    )
    if dry_run or len(tests_to_run) <= 1:
        return _run_sequential_tests(
            tests_to_run,
            settings,
            dry_run,
            instruction_ref,
            harness,
            judge_harness,
            on_result,
        )
    max_workers = max_workers_override or settings.get(
        "parallel_workers", DEFAULT_PARALLEL_WORKERS
    )
    return _run_parallel_tests(
        tests_to_run,
        settings,
        instruction_ref,
        harness,
        judge_harness,
        max_workers,
        on_result,
    )


def _run_smoke_test(config, settings, dry_run, harness, judge_harness, on_result):
    smoke = config.get("smoke_test")
    if not smoke:
        return []
    result = run_test(
        smoke,
        settings,
        dry_run,
        "smoke",
        harness=harness,
        judge_harness=judge_harness,
    )
    if on_result:
        on_result(result)
    return [result]


def _run_sequential_tests(
    tests_to_run, settings, dry_run, instruction_ref, harness, judge_harness, on_result
):
    results = [
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
    if on_result:
        for result in results:
            on_result(result)
    return results


def _run_parallel_tests(
    tests_to_run,
    settings: dict,
    instruction_ref: str | None,
    harness: str,
    judge_harness: str,
    max_workers: int,
    on_result,
) -> list[TestResult]:
    results_by_index = {}
    reporter = EvaluationProgressReporter(len(tests_to_run), max_workers)
    reporter.announce_start()
    executor = ThreadPoolExecutor(max_workers=max_workers)
    future_to_index = {}
    next_index = 0

    def submit_next():
        nonlocal next_index
        if next_index >= len(tests_to_run):
            return
        test, category_name = tests_to_run[next_index]
        future = executor.submit(
            run_test,
            test,
            settings,
            False,
            category_name,
            instruction_ref,
            harness,
            judge_harness,
        )
        future_to_index[future] = next_index
        next_index += 1

    try:
        for _ in range(min(max_workers, len(tests_to_run))):
            submit_next()
        while future_to_index:
            completed, _ = wait(future_to_index, return_when=FIRST_COMPLETED)
            _record_completed_futures(
                completed,
                future_to_index,
                results_by_index,
                reporter,
                on_result,
                submit_next,
            )
    except BaseException:
        for future in future_to_index:
            future.cancel()
        executor.shutdown(wait=False, cancel_futures=True)
        raise
    else:
        executor.shutdown()
    reporter.announce_finish()
    return [results_by_index[index] for index in range(len(tests_to_run))]


def _record_completed_futures(
    completed,
    future_to_index: dict,
    results_by_index: dict,
    reporter: EvaluationProgressReporter,
    on_result,
    submit_next,
) -> None:
    for future in completed:
        index = future_to_index.pop(future)
        result = future.result()
        results_by_index[index] = result
        reporter.record(result)
        if on_result:
            on_result(result)
        submit_next()
