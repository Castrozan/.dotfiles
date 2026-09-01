from run_evals_baseline_policy import (
    REQUIRED_HUMANIZE_PROFILE,
    baseline_evidence_failures,
)

EXECUTION_PROFILE = {
    "subject": {"harness": "claude", "model": "sonnet", "reasoning_effort": "high"},
    "judge": {"harness": "claude", "model": "opus", "reasoning_effort": None},
}
CURRENT_TEST_FINGERPRINTS = {
    "communication::communication_case": "communication-sha",
    "skills/humanize/reader_recovery::recovery_case": "recovery-sha",
}


def valid_baseline():
    fingerprints = {"suite": "suite-sha", "instructions": "instruction-sha"}
    humanize_fingerprints = {
        "suite": "humanize-suite-sha",
        "instructions": "humanize-instruction-sha",
    }
    return {
        "categories": {
            "communication": {
                "passed": 15,
                "failed": 1,
                "tests": [
                    {
                        "name": "communication_case",
                        "passed": True,
                        "fingerprint": "communication-sha",
                    }
                ],
            },
            "skills/humanize/reader_recovery": {
                "passed": 21,
                "failed": 0,
                "tests": [
                    {
                        "name": "recovery_case",
                        "passed": True,
                        "fingerprint": "recovery-sha",
                    }
                ],
            },
        },
        "fingerprints": fingerprints,
        "execution_profile": EXECUTION_PROFILE,
        "evidence_profiles": {
            REQUIRED_HUMANIZE_PROFILE: {
                "epochs": 3,
                "candidate_pass_rate": 0.95,
                "delta": 0.05,
                "candidate_hard_failures": [],
                "fingerprints": humanize_fingerprints,
                "execution_profile": EXECUTION_PROFILE,
            }
        },
    }


def test_baseline_evidence_accepts_current_repeated_recovery_measurement():
    baseline = valid_baseline()
    profile_fingerprints = baseline["evidence_profiles"][REQUIRED_HUMANIZE_PROFILE][
        "fingerprints"
    ]
    assert (
        baseline_evidence_failures(
            baseline,
            CURRENT_TEST_FINGERPRINTS,
            profile_fingerprints,
            set(baseline["categories"]),
            EXECUTION_PROFILE,
        )
        == []
    )


def test_baseline_evidence_rejects_stale_sources_and_missing_coverage():
    baseline = valid_baseline()
    del baseline["categories"]["communication"]
    baseline["evidence_profiles"][REQUIRED_HUMANIZE_PROFILE]["epochs"] = 1
    failures = baseline_evidence_failures(
        baseline,
        {
            **CURRENT_TEST_FINGERPRINTS,
            "skills/humanize/reader_recovery::recovery_case": "changed-sha",
        },
        baseline["evidence_profiles"][REQUIRED_HUMANIZE_PROFILE]["fingerprints"],
        set(baseline["categories"]),
        EXECUTION_PROFILE,
    )
    assert any("communication" in failure for failure in failures)
    assert any("stale evaluation tests" in failure for failure in failures)
    assert any("at least 3 epochs" in failure for failure in failures)


def test_baseline_evidence_rejects_weak_or_empty_communication_coverage():
    baseline = valid_baseline()
    profile_fingerprints = baseline["evidence_profiles"][REQUIRED_HUMANIZE_PROFILE][
        "fingerprints"
    ]
    baseline["categories"]["communication"] = {"passed": 12, "failed": 4}
    failures = baseline_evidence_failures(
        baseline,
        CURRENT_TEST_FINGERPRINTS,
        profile_fingerprints,
        set(baseline["categories"]),
        EXECUTION_PROFILE,
    )
    assert any("Communication pass rate" in failure for failure in failures)

    baseline["categories"]["communication"] = {"passed": 0, "failed": 0}
    failures = baseline_evidence_failures(
        baseline,
        CURRENT_TEST_FINGERPRINTS,
        profile_fingerprints,
        set(baseline["categories"]),
        EXECUTION_PROFILE,
    )
    assert any("contains no results" in failure for failure in failures)


def test_baseline_evidence_rejects_missing_and_obsolete_category_buckets():
    baseline = valid_baseline()
    baseline["categories"]["obsolete"] = {"passed": 1, "failed": 0}
    profile_fingerprints = baseline["evidence_profiles"][REQUIRED_HUMANIZE_PROFILE][
        "fingerprints"
    ]

    failures = baseline_evidence_failures(
        baseline,
        CURRENT_TEST_FINGERPRINTS,
        profile_fingerprints,
        {
            "communication",
            "skills/humanize/reader_recovery",
            "new_category",
        },
        EXECUTION_PROFILE,
    )

    assert any(
        "missing current evaluation categories" in failure for failure in failures
    )
    assert any("obsolete evaluation categories" in failure for failure in failures)
