from run_evals_baseline import (
    COMPLIANCE_CATEGORIES,
    build_baseline_from_results,
    compliance_passed_and_total,
)
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
