import json


def write_document(destination, contents):
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(contents)


def write_eval_suite(repository_root, relative_path, case_names, graded_by_judge):
    assertion = "llm_judge" if graded_by_judge else "contains"
    cases = "".join(
        f"  - name: {case_name}\n    assertions:\n      {assertion}: whatever\n"
        for case_name in case_names
    )
    write_document(repository_root / relative_path, f"tests:\n{cases}")


def build_synthetic_evidence_repository(repository_root):
    write_eval_suite(
        repository_root,
        "agent-harness/quality/evaluations/evals/adversarial.yaml",
        ["one", "two"],
        True,
    )
    write_eval_suite(
        repository_root,
        "agent-harness/quality/evaluations/evals/core_rules.yaml",
        ["three"],
        True,
    )
    write_eval_suite(
        repository_root,
        "agent-harness/quality/evaluations/evals/hooks.yaml",
        ["four"],
        False,
    )
    write_eval_suite(
        repository_root,
        "agent-harness/agent-instructions/skills/nix/__tests__/evals/rebuild.yaml",
        ["five"],
        False,
    )
    write_document(
        repository_root
        / "agent-harness/quality/evaluations/calibration/judge_calibration.yaml",
        "recorded_agreement:\n  cases: 24\n  accuracy: 0.917\n  cohens_kappa: 0.833\n",
    )
    write_document(
        repository_root / "agent-harness/quality/evaluations/baseline.json",
        json.dumps({"pass_rate": 0.9}),
    )
    write_document(
        repository_root
        / "agent-harness/quality/evaluations/instruction-loading-experiment.json",
        json.dumps(
            {
                "categories": {
                    "workflow_compliance": {"paired_tests": 8},
                    "core_rules": {"paired_tests": 12},
                }
            }
        ),
    )
    return repository_root


def practice_named(practices, practice_name):
    return next(
        practice for practice in practices if practice["practice"] == practice_name
    )
