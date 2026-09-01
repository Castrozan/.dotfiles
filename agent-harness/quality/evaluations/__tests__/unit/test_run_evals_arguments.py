import sys

import pytest

from run_evals_arguments import parse_arguments


@pytest.mark.parametrize(
    "arguments",
    (
        ["run-evals.py", "--dry-run", "--save-baseline"],
        [
            "run-evals.py",
            "--dry-run",
            "--ab",
            "--compare-ref",
            "main",
            "--category",
            "communication",
            "--epochs",
            "3",
            "--save-ab-profile",
        ],
        ["run-evals.py", "--test", "one", "--save-baseline"],
        ["run-evals.py", "--harness", "claude", "--save-baseline"],
        [
            "run-evals.py",
            "--harness",
            "opencode",
            "--ab",
            "--compare-ref",
            "main",
            "--category",
            "communication",
            "--epochs",
            "3",
            "--save-ab-profile",
        ],
    ),
)
def test_synthetic_or_partial_results_cannot_be_saved_as_baseline_evidence(
    arguments, monkeypatch
):
    monkeypatch.setattr(sys, "argv", arguments)

    with pytest.raises(SystemExit):
        parse_arguments()


def test_canonical_codex_subject_and_judge_can_save_evidence(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run-evals.py",
            "--harness",
            "codex",
            "--judge-harness",
            "codex",
            "--save-baseline",
        ],
    )

    arguments = parse_arguments()

    assert arguments.harness == "codex"
    assert arguments.judge_harness == "codex"
