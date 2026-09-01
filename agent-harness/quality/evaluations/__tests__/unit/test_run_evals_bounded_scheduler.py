from concurrent.futures import Future

import run_evals_suite_runner
from run_evals_suite_runner import run_tests
from run_evals_test_runner import TestResult


def echo_run_test(
    test,
    settings,
    dry_run,
    authored_category="other",
    instruction_ref=None,
    harness="claude",
    judge_harness="claude",
):
    return TestResult(
        name=test["name"],
        passed=True,
        duration=0.0,
        output=test["prompt"],
        assertions_failed=[],
        category=authored_category,
    )


def test_run_tests_checkpoints_each_finished_result(monkeypatch):
    monkeypatch.setattr(run_evals_suite_runner, "run_test", echo_run_test)
    config = {
        "settings": {"parallel_workers": 2},
        "tests": {
            "one": [{"name": "first", "prompt": "a"}],
            "two": [{"name": "second", "prompt": "b"}],
        },
    }
    checkpointed = []

    results = run_tests(config, on_result=checkpointed.append)

    assert {result.name for result in results} == {"first", "second"}
    assert {result.name for result in checkpointed} == {"first", "second"}


def test_parallel_scheduler_only_queues_the_worker_bound(monkeypatch):
    submitted = []
    observed_queue_sizes = []

    class ImmediateExecutor:
        def __init__(self, max_workers):
            self.max_workers = max_workers

        def submit(self, function, *arguments):
            future = Future()
            future.set_result(function(*arguments))
            submitted.append(future)
            return future

        def shutdown(self, wait=True, cancel_futures=False):
            return None

    def observe_wait(futures, return_when):
        observed_queue_sizes.append(len(submitted))
        future = next(iter(futures))
        return {future}, set(futures) - {future}

    monkeypatch.setattr(run_evals_suite_runner, "run_test", echo_run_test)
    monkeypatch.setattr(run_evals_suite_runner, "ThreadPoolExecutor", ImmediateExecutor)
    monkeypatch.setattr(run_evals_suite_runner, "wait", observe_wait)
    config = {
        "settings": {"parallel_workers": 2},
        "tests": {
            "communication": [
                {"name": f"test-{index}", "prompt": str(index)} for index in range(5)
            ]
        },
    }

    results = run_tests(config)

    assert observed_queue_sizes[0] == 2
    assert len(results) == 5
