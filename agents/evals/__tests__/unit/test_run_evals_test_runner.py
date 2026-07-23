import run_evals_test_runner
from run_evals_test_runner import TestResult, run_tests


def _echo_run_test(test, settings, dry_run, authored_category="other"):
    return TestResult(
        name=test["name"],
        passed=True,
        duration=0.0,
        output=test["prompt"],
        assertions_failed=[],
        category=authored_category,
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


def test_run_tests_tags_each_result_with_its_authored_category(monkeypatch):
    monkeypatch.setattr(run_evals_test_runner, "run_test", _echo_run_test)
    config = {
        "settings": {"parallel_workers": 2},
        "tests": {
            "workflow_compliance": [
                {"name": "a", "prompt": "p"},
                {"name": "b", "prompt": "p"},
            ],
            "skill_routing": [{"name": "c", "prompt": "p"}],
        },
    }

    results = run_tests(config)

    category_by_name = {result.name: result.category for result in results}
    assert category_by_name == {
        "a": "workflow_compliance",
        "b": "workflow_compliance",
        "c": "skill_routing",
    }


def test_serial_single_test_still_carries_authored_category(monkeypatch):
    monkeypatch.setattr(run_evals_test_runner, "run_test", _echo_run_test)
    config = {
        "settings": {},
        "tests": {"core_rules": [{"name": "only", "prompt": "p"}]},
    }

    results = run_tests(config)

    assert len(results) == 1
    assert results[0].category == "core_rules"
