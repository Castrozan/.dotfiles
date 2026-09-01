from run_evals_baseline_policy import (
    REQUIRED_HUMANIZE_PROFILE,
    baseline_evidence_failures,
)
from run_evals_fingerprint import (
    evaluation_category_names,
    evaluation_fingerprints,
    humanize_recovery_fingerprints,
)

EXECUTION_PROFILE = {
    "subject": {"harness": "claude", "model": "sonnet", "reasoning_effort": "high"},
    "judge": {"harness": "claude", "model": "opus", "reasoning_effort": None},
}


def valid_baseline():
    fingerprints = {"suite": "suite-sha", "instructions": "instruction-sha"}
    humanize_fingerprints = {
        "suite": "humanize-suite-sha",
        "instructions": "humanize-instruction-sha",
    }
    return {
        "categories": {
            "communication": {"passed": 15, "failed": 1},
            "skills/humanize/reader_recovery": {"passed": 21, "failed": 0},
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
            baseline["fingerprints"],
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
        {"suite": "new-suite", "instructions": "instruction-sha"},
        baseline["evidence_profiles"][REQUIRED_HUMANIZE_PROFILE]["fingerprints"],
        set(baseline["categories"]),
        EXECUTION_PROFILE,
    )
    assert any("communication" in failure for failure in failures)
    assert any("fingerprint" in failure for failure in failures)
    assert any("at least 3 epochs" in failure for failure in failures)


def test_baseline_evidence_rejects_weak_or_empty_communication_coverage():
    baseline = valid_baseline()
    profile_fingerprints = baseline["evidence_profiles"][REQUIRED_HUMANIZE_PROFILE][
        "fingerprints"
    ]
    baseline["categories"]["communication"] = {"passed": 12, "failed": 4}
    failures = baseline_evidence_failures(
        baseline,
        baseline["fingerprints"],
        profile_fingerprints,
        set(baseline["categories"]),
        EXECUTION_PROFILE,
    )
    assert any("Communication pass rate" in failure for failure in failures)

    baseline["categories"]["communication"] = {"passed": 0, "failed": 0}
    failures = baseline_evidence_failures(
        baseline,
        baseline["fingerprints"],
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
        baseline["fingerprints"],
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


def test_evaluation_fingerprint_changes_with_suite_and_instruction_content(tmp_path):
    suite_directory = tmp_path / "agent-harness/quality/evaluations/evals"
    skill_directory = tmp_path / "agent-harness/agent-instructions/skills/example"
    suite_directory.mkdir(parents=True)
    skill_directory.mkdir(parents=True)
    skill_path = skill_directory / "SKILL.md"
    skill_path.write_text("policy one")
    suite_path = suite_directory / "example.yaml"
    suite_path.write_text(
        "tests:\n  - name: x\n"
        "    skill_path: agent-harness/agent-instructions/skills/example/SKILL.md\n"
    )

    original = evaluation_fingerprints(tmp_path)
    skill_path.write_text("policy two")
    instruction_changed = evaluation_fingerprints(tmp_path)
    suite_path.write_text(suite_path.read_text() + "    prompt: hi\n")
    suite_changed = evaluation_fingerprints(tmp_path)

    assert original["instructions"] != instruction_changed["instructions"]
    assert instruction_changed["suite"] != suite_changed["suite"]


def test_humanize_profile_fingerprint_ignores_unrelated_eval_suites(tmp_path):
    recovery_directory = (
        tmp_path / "agent-harness/agent-instructions/skills/humanize/__tests__/evals"
    )
    skill_directory = recovery_directory.parents[1]
    eval_directory = tmp_path / "agent-harness/quality/evaluations/evals"
    calibration_directory = tmp_path / "agent-harness/quality/evaluations/calibration"
    recovery_directory.mkdir(parents=True)
    eval_directory.mkdir(parents=True)
    calibration_directory.mkdir(parents=True)
    (skill_directory / "SKILL.md").write_text("reader policy")
    (recovery_directory / "reader_recovery.yaml").write_text(
        "tests:\n  - name: recovery\n"
        "    skill_path: agent-harness/agent-instructions/skills/humanize/SKILL.md\n"
    )
    unrelated = eval_directory / "unrelated.yaml"
    unrelated.write_text("tests: []\n")
    calibration = calibration_directory / "judge_calibration.yaml"
    calibration.write_text("cases: []\n")

    original = humanize_recovery_fingerprints(tmp_path)
    unrelated.write_text("tests:\n  - name: unrelated\n")

    assert humanize_recovery_fingerprints(tmp_path) == original
    runner = eval_directory.parent / "run_evals_judge.py"
    runner.write_text("def grade(): return True\n")
    assert humanize_recovery_fingerprints(tmp_path) != original
    runner.unlink()
    calibration.write_text("cases:\n  - name: changed\n")
    assert humanize_recovery_fingerprints(tmp_path) != original


def test_evaluation_category_inventory_tracks_regular_and_skill_suites(tmp_path):
    eval_directory = tmp_path / "agent-harness/quality/evaluations/evals"
    skill_eval_directory = (
        tmp_path / "agent-harness/agent-instructions/skills/example/__tests__/evals"
    )
    eval_directory.mkdir(parents=True)
    skill_eval_directory.mkdir(parents=True)
    (eval_directory / "communication.yaml").write_text("tests: []\n")
    (eval_directory / "settings.yaml").write_text("settings: {}\n")
    (skill_eval_directory / "recovery.yaml").write_text("tests: []\n")

    assert evaluation_category_names(tmp_path) == {
        "communication",
        "skills/example/recovery",
    }
