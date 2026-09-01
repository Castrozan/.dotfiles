from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

from run_evals_progress import EvaluationProgressReporter
from run_evals_test_runner import TestResult, run_test

DEFAULT_PARALLEL_WORKERS = 2


def selected_tests(
    config: dict,
    category: str | None,
    test_name: str | None,
    selected_test_keys: set[str] | None = None,
) -> list:
    selected = []
    for category_name, tests in config.get("tests", {}).items():
        if category and category_name != category:
            continue
        for test in tests:
            key = f"{category_name}::{test['name']}"
            if (not test_name or test["name"] == test_name) and (
                selected_test_keys is None or key in selected_test_keys
            ):
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
    selected_test_keys: set[str] | None = None,
    on_result=None,
) -> list[TestResult]:
    settings = config.get("settings", {})
    if smoke_only:
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
    tests_to_run = selected_tests(
        config, category, test_name, selected_test_keys=selected_test_keys
    )
    if dry_run or len(tests_to_run) <= 1:
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
    max_workers = max_workers_override or settings.get(
        "parallel_workers", DEFAULT_PARALLEL_WORKERS
    )
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
            for future in completed:
                index = future_to_index.pop(future)
                result = future.result()
                results_by_index[index] = result
                reporter.record(result)
                if on_result:
                    on_result(result)
                submit_next()
    except BaseException:
        for future in future_to_index:
            future.cancel()
        executor.shutdown(wait=False, cancel_futures=True)
        raise
    else:
        executor.shutdown()
    reporter.announce_finish()
    return [results_by_index[index] for index in range(len(tests_to_run))]
