import json

import run_evals_baseline_record
from run_evals_baseline import compliance_passed_and_total
from run_evals_baseline_record import (
    merge_baseline_categories,
    merge_baseline_snapshot,
)
from run_evals_baseline_thresholds import COMPLIANCE_CATEGORIES

EXECUTION_PROFILE = {
    "subject": {"harness": "claude", "model": "sonnet", "reasoning_effort": "high"},
    "judge": {"harness": "claude", "model": "opus", "reasoning_effort": None},
}
TOKEN_USAGE = {"input_tokens": 100, "output_tokens": 50}


def test_off_prefix_compliance_test_counts_toward_the_floor():
    categories = {"workflow_compliance": {"passed": 0, "failed": 1}}
    passed, total = compliance_passed_and_total(categories)

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
        "execution_profile": EXECUTION_PROFILE,
        "categories": {
            "existing": {
                "passed": 2,
                "failed": 1,
                "tests": [
                    {
                        "name": "retained",
                        "passed": True,
                        "generated_at": "2026-07-23T03:26:24+00:00",
                    }
                ],
            },
            "communication": {"passed": 1, "failed": 1, "tests": []},
        },
    }
    replacement = {"passed": 3, "failed": 0, "tests": []}

    merged = merge_baseline_categories(
        baseline, {"communication": replacement}, EXECUTION_PROFILE, TOKEN_USAGE
    )

    assert merged["categories"]["existing"]["failed"] == 1
    assert merged["categories"]["communication"] == replacement
    assert merged["total_passed"] == 5
    assert merged["total_tests"] == 6
    assert merged["generated_at"] != baseline["generated_at"]
    assert merged["oldest_evidence_at"] == "2026-07-23T03:26:24+00:00"


def test_selected_category_snapshot_merges_into_the_committed_baseline(
    tmp_path, monkeypatch
):
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        json.dumps(
            {
                "execution_profile": EXECUTION_PROFILE,
                "categories": {"existing": {"passed": 2, "failed": 0, "tests": []}},
            }
        )
    )
    monkeypatch.setattr(run_evals_baseline_record, "BASELINE_PATH", baseline_path)
    monkeypatch.setattr(
        run_evals_baseline_record,
        "evaluation_category_names",
        lambda: {"existing", "communication"},
    )

    merged = merge_baseline_snapshot(
        {"categories": {"communication": {"passed": 3, "failed": 1, "tests": []}}},
        EXECUTION_PROFILE,
        TOKEN_USAGE,
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
        "minimum_current_evidence": 2,
        "execution_profile": EXECUTION_PROFILE,
        "categories": {
            "obsolete": {
                "passed": 1,
                "failed": 0,
                "tests": [{"name": "gone", "passed": True}],
            },
            "communication": {
                "passed": 1,
                "failed": 0,
                "tests": [{"name": "kept", "passed": True}],
            },
        },
    }

    merged = merge_baseline_categories(
        baseline,
        {
            "communication": {
                "passed": 1,
                "failed": 0,
                "tests": [{"name": "kept", "passed": True}],
            }
        },
        EXECUTION_PROFILE,
        TOKEN_USAGE,
    )

    assert set(merged["categories"]) == {"communication"}
    assert merged["total_passed"] == 1
    assert merged["total_tests"] == 1
    assert merged["minimum_current_evidence"] == 1
