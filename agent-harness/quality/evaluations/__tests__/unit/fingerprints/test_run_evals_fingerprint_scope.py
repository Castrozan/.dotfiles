from runner.baseline.run_evals_fingerprint import (
    evaluation_category_names,
    evaluation_fingerprints,
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
