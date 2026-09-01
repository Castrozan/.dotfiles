from run_evals_fingerprint import (
    evaluation_category_names,
    evaluation_fingerprints,
    humanize_recovery_fingerprints,
)


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
    checkpoint = eval_directory.parent / "run_evals_baseline_incremental.py"
    checkpoint.write_text("def checkpoint(): return True\n")
    assert humanize_recovery_fingerprints(tmp_path) == original
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
