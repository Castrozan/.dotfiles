import run_evals_test_runner
from run_evals_test_runner import TestResult, run_tests


def _echo_run_test(test, settings, dry_run):
    return TestResult(
        name=test["name"],
        passed=True,
        duration=0.0,
        output=test["prompt"],
        assertions_failed=[],
    )


def test_parallel_run_keeps_results_for_duplicate_test_names(monkeypatch):
    monkeypatch.setattr(run_evals_test_runner, "run_test", _echo_run_test)
    config = {
        "settings": {"parallel_workers": 2},
        "tests": {
            "category_one": [{"name": "dup", "prompt": "prompt-A"}],
            "category_two": [{"name": "dup", "prompt": "prompt-B"}],
        },
    }

    results = run_tests(config)

    assert len(results) == 2
    assert {result.output for result in results} == {"prompt-A", "prompt-B"}
