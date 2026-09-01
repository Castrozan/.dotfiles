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
        ["run-evals.py", "--harness", "claude", "--save-baseline"],
        ["run-evals.py", "--smoke", "--save-baseline"],
        ["run-evals.py", "--all-tests"],
        ["run-evals.py", "--epochs", "3", "--save-baseline"],
        [
            "run-evals.py",
            "--epochs",
            "3",
            "--save-baseline",
            "--all-tests",
            "--test",
            "one",
        ],
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


def test_one_affected_test_can_refresh_its_baseline_result(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["run-evals.py", "--test", "one", "--save-baseline"],
    )

    arguments = parse_arguments()

    assert arguments.test == "one"
    assert arguments.save_baseline is True


def test_affected_inventory_is_a_read_only_mode(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["run-evals.py", "--list-affected"])

    arguments = parse_arguments()

    assert arguments.list_affected is True
    assert arguments.save_baseline is False
