import json

from reporting.run_evals_run_record import open_run_record
from runner.execution.run_evals_test_runner import TestResult


def _result(name, output, passed=True, failures=None, error=None):
    return TestResult(
        name=name,
        passed=passed,
        duration=1.5,
        output=output,
        assertions_failed=failures or [],
        error=error,
        category="skill_routing",
    )


def test_each_case_lands_as_one_json_line_with_its_full_output(tmp_path):
    long_output = "x" * 2000
    run_record = open_run_record(tmp_path)

    run_record.record(_result("first", long_output))
    run_record.record(
        _result("second", "docs", passed=False, failures=["Expected 'wellput'"]),
        epoch=2,
    )

    lines = run_record.results_path.read_text().splitlines()
    rows = [json.loads(line) for line in lines]
    assert run_record.results_path.parent.parent == tmp_path
    assert rows[0]["output"] == long_output
    assert rows[0]["epoch"] == 1
    assert rows[1] == {
        "category": "skill_routing",
        "name": "second",
        "epoch": 2,
        "passed": False,
        "duration": 1.5,
        "assertions_failed": ["Expected 'wellput'"],
        "error": None,
        "output": "docs",
    }


def test_separate_runs_never_share_a_results_file(tmp_path):
    first = open_run_record(tmp_path)
    second = open_run_record(tmp_path)

    assert first.results_path != second.results_path
