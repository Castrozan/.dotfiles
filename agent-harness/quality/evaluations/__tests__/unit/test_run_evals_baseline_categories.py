import json

import pytest

import run_evals_baseline_record
from run_evals_baseline import compliance_passed_and_total
from run_evals_baseline_record import (
    build_baseline_from_results,
    merge_baseline_categories,
    merge_baseline_snapshot,
    repeated_outcomes_category_bucket,
)
from run_evals_baseline_thresholds import COMPLIANCE_CATEGORIES
from run_evals_test_runner import TestResult


def _result(name, passed, category):
    return TestResult(
        name=name,
        passed=passed,
        duration=0.0,
        output="",
        assertions_failed=[] if passed else ["failed"],
        category=category,
    )


def test_build_baseline_buckets_by_authored_category_not_name_prefix():
    results = [
        _result("obeys_the_commit_sequence", True, "workflow_compliance"),
        _result("rebuilds_after_every_edit", True, "workflow_compliance"),
        _result("desktop_control_over_keyboard", False, "skill_routing"),
    ]

    baseline = build_baseline_from_results(results)

    assert set(baseline["categories"]) == {"workflow_compliance", "skill_routing"}
    assert baseline["categories"]["workflow_compliance"]["passed"] == 2
    assert baseline["categories"]["workflow_compliance"]["failed"] == 0
    assert baseline["categories"]["skill_routing"]["failed"] == 1


def test_off_prefix_compliance_test_counts_toward_the_floor():
    results = [_result("obeys_the_commit_sequence", False, "workflow_compliance")]

    baseline = build_baseline_from_results(results)
    passed, total = compliance_passed_and_total(baseline["categories"])

    assert total == 1
    assert passed == 0


def test_compliance_rate_sums_the_authored_compliance_set_and_excludes_the_rest():
    categories = {
        "instruction_compliance": {"passed": 8, "failed": 0},
        "workflow_compliance": {"passed": 7, "failed": 1},
        "rebuild_mandate": {"passed": 4, "failed": 0},
        "delegation": {"passed": 8, "failed": 0},
        "core_rules": {"passed": 11, "failed": 1},
        "skill_routing": {"passed": 50, "failed": 5},
    }

    passed, total = compliance_passed_and_total(categories)

    assert total == 40
    assert passed == 38


def test_compliance_categories_are_the_obedience_suites():
    assert COMPLIANCE_CATEGORIES == {
        "instruction_compliance",
        "workflow_compliance",
        "rebuild_mandate",
        "delegation",
        "core_rules",
    }


def test_category_refresh_preserves_other_baseline_categories(monkeypatch):
    monkeypatch.setattr(
        run_evals_baseline_record,
        "evaluation_category_names",
        lambda: {"existing", "communication"},
    )
    baseline = {
        "generated_at": "2026-07-24T03:26:24+00:00",
        "categories": {
            "existing": {"passed": 2, "failed": 1, "tests": []},
            "communication": {"passed": 1, "failed": 1, "tests": []},
        },
    }
    replacement = {"passed": 3, "failed": 0, "tests": []}

    merged = merge_baseline_categories(baseline, {"communication": replacement})

    assert merged["categories"]["existing"]["failed"] == 1
    assert merged["categories"]["communication"] == replacement
    assert merged["total_passed"] == 5
    assert merged["total_tests"] == 6
    assert merged["generated_at"] == baseline["generated_at"]


def test_repeated_outcomes_become_a_majority_graded_category_bucket():
    bucket = repeated_outcomes_category_bucket(
        {
            "category::stable": [True, True, True],
            "category::flaky": [True, False, True],
            "category::failed": [False, False, False],
        }
    )

    assert bucket["passed"] == 2
    assert bucket["failed"] == 1
    assert bucket["tests"][1] == {
        "name": "flaky",
        "passed": True,
        "passes": 2,
        "samples": 3,
    }


def test_selected_category_snapshot_merges_into_the_committed_baseline(
    tmp_path, monkeypatch
):
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        json.dumps(
            {"categories": {"existing": {"passed": 2, "failed": 0, "tests": []}}}
        )
    )
    monkeypatch.setattr(run_evals_baseline_record, "BASELINE_PATH", baseline_path)
    monkeypatch.setattr(
        run_evals_baseline_record,
        "evaluation_category_names",
        lambda: {"existing", "communication"},
    )

    merged = merge_baseline_snapshot(
        {"categories": {"communication": {"passed": 3, "failed": 1, "tests": []}}}
    )

    assert set(merged["categories"]) == {"existing", "communication"}
    assert merged["total_tests"] == 6


def test_category_refresh_prunes_categories_without_current_suites(monkeypatch):
    monkeypatch.setattr(
        run_evals_baseline_record,
        "evaluation_category_names",
        lambda: {"communication"},
    )
    baseline = {
        "categories": {
            "obsolete": {"passed": 2, "failed": 0, "tests": []},
            "communication": {"passed": 1, "failed": 1, "tests": []},
        }
    }

    merged = merge_baseline_categories(
        baseline,
        {"communication": {"passed": 3, "failed": 0, "tests": []}},
    )

    assert set(merged["categories"]) == {"communication"}
    assert merged["total_passed"] == 3
    assert merged["total_tests"] == 3


def test_baseline_save_rejects_invocation_errors(tmp_path, monkeypatch):
    monkeypatch.setattr(
        run_evals_baseline_record, "BASELINE_PATH", tmp_path / "baseline.json"
    )
    result = _result("provider_limit", False, "communication")
    result.error = "session limit reached"

    with pytest.raises(RuntimeError, match="baseline evidence has invocation errors"):
        run_evals_baseline_record.save_baseline([result])

    assert not run_evals_baseline_record.BASELINE_PATH.exists()
