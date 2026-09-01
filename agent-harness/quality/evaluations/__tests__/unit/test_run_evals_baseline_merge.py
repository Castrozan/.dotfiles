from run_evals_baseline_incremental import merge_baseline_results
from run_evals_execution_profile import execution_profile_identifier
from run_evals_test_runner import TestResult


EXECUTION_PROFILE = {
    "subject": {"harness": "codex", "model": "gpt-5.6-sol", "reasoning_effort": "high"},
    "judge": {"harness": "codex", "model": "gpt-5.6-luna", "reasoning_effort": "low"},
}


def result(name: str, passed: bool):
    return TestResult(
        name=name,
        passed=passed,
        duration=0.0,
        output="",
        assertions_failed=[] if passed else ["failed"],
        category="communication",
    )


def test_per_test_merge_preserves_historical_results_and_prunes_obsolete_tests():
    fingerprints = {
        "communication::first": "current-first-fingerprint",
        "communication::second": "second-fingerprint",
    }
    baseline = {
        "categories": {
            "communication": {
                "tests": [
                    {
                        "name": "first",
                        "passed": True,
                        "fingerprint": "historical-first-fingerprint",
                        "generated_at": "2026-08-30T00:00:00+00:00",
                    },
                    {
                        "name": "stale",
                        "passed": False,
                        "fingerprint": "stale-fingerprint",
                        "generated_at": "2026-08-30T00:00:00+00:00",
                    },
                ]
            },
            "obsolete": {
                "tests": [
                    {
                        "name": "gone",
                        "passed": True,
                        "fingerprint": "gone-fingerprint",
                        "generated_at": "2026-08-30T00:00:00+00:00",
                    }
                ]
            },
        },
    }

    merged = merge_baseline_results(
        baseline,
        [result("second", False)],
        EXECUTION_PROFILE,
        {"subject": {"codex": {"invocations": 1}}},
        fingerprints,
        "2026-08-31T00:00:00+00:00",
    )

    assert set(merged["categories"]) == {"communication"}
    assert merged["categories"]["communication"]["tests"] == [
        {
            "name": "first",
            "passed": True,
            "fingerprint": "historical-first-fingerprint",
            "generated_at": "2026-08-30T00:00:00+00:00",
        },
        {
            "name": "second",
            "passed": False,
            "fingerprint": "second-fingerprint",
            "generated_at": "2026-08-31T00:00:00+00:00",
            "execution_profile_id": execution_profile_identifier(EXECUTION_PROFILE),
            "run_source": {"kind": "checkpoint", "git_commit": merged["git_commit"]},
        },
    ]
    assert merged["total_passed"] == 1
    assert merged["total_tests"] == 2
    assert merged["generated_at"] == "2026-08-31T00:00:00+00:00"
    assert merged["oldest_evidence_at"] == "2026-08-30T00:00:00+00:00"
    assert merged["minimum_current_evidence"] == 1
    assert merged["execution_profiles"] == {
        execution_profile_identifier(EXECUTION_PROFILE): EXECUTION_PROFILE
    }
