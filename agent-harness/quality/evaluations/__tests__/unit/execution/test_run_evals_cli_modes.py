import contextlib
import json
from types import SimpleNamespace

from reporting import run_evals_run_record
from runner import run_evals_cli_modes
from runner.execution.run_evals_test_runner import TestResult


def test_judge_calibration_honors_the_requested_worker_limit(monkeypatch):
    observed = {}
    arguments = SimpleNamespace(judge_harness="codex", workers=1, epochs=1)
    config = {
        "settings": {
            "judge_models": {"codex": "gpt-5.6-luna"},
            "judge_reasoning_efforts": {"codex": "low"},
            "timeout_seconds": 120,
        }
    }
    monkeypatch.setattr(
        run_evals_cli_modes, "build_provider_invoker", lambda *arguments: None
    )
    monkeypatch.setattr(run_evals_cli_modes, "build_llm_judge", lambda *arguments: None)
    monkeypatch.setattr(run_evals_cli_modes, "load_calibration_cases", lambda: [])
    monkeypatch.setattr(
        run_evals_cli_modes,
        "judge_agreement",
        lambda cases, judge, max_workers: observed.update(workers=max_workers) or {},
    )
    monkeypatch.setattr(run_evals_cli_modes, "print_calibration_summary", bool)
    monkeypatch.setattr(
        run_evals_cli_modes, "collect_and_print_provider_usage", lambda: {}
    )

    run_evals_cli_modes.run_judge_calibration(config, arguments)

    assert observed["workers"] == 1


def test_repeated_runs_record_every_case_under_its_epoch(monkeypatch, tmp_path):
    def one_case_run(config, **options):
        result = TestResult("case", True, 0.1, "full output", [], category="c")
        options["on_result"](result)
        return [result]

    arguments = SimpleNamespace(
        epochs=2,
        category="c",
        test=None,
        dry_run=False,
        smoke=False,
        workers=1,
        harness="codex",
        judge_harness="codex",
        partition=None,
        save_baseline=False,
    )
    monkeypatch.setattr(run_evals_cli_modes, "run_tests", one_case_run)
    monkeypatch.setattr(
        run_evals_cli_modes, "temporary_eval_worktree", contextlib.nullcontext
    )
    monkeypatch.setattr(
        run_evals_cli_modes, "evaluation_test_fingerprints", lambda config: {}
    )
    monkeypatch.setattr(
        run_evals_cli_modes,
        "run_record_for",
        lambda dry_run: run_evals_run_record.open_run_record(tmp_path),
    )
    monkeypatch.setattr(
        run_evals_cli_modes, "collect_and_print_provider_usage", lambda: {}
    )

    run_evals_cli_modes.run_repeated_evaluation({}, arguments, {})

    (results_path,) = tmp_path.glob("*/results.jsonl")
    rows = [json.loads(line) for line in results_path.read_text().splitlines()]
    assert [(row["name"], row["epoch"]) for row in rows] == [("case", 1), ("case", 2)]
    assert rows[0]["output"] == "full output"


def test_judge_calibration_grades_the_corpus_once_per_epoch(monkeypatch, capsys):
    passes = iter(
        [
            {"verdicts": {"a": True, "b": True}, "meets_gate": True},
            {"verdicts": {"a": True, "b": False}, "meets_gate": True},
        ]
    )
    arguments = SimpleNamespace(judge_harness="codex", workers=1, epochs=2)
    monkeypatch.setattr(
        run_evals_cli_modes, "build_provider_invoker", lambda *arguments: None
    )
    monkeypatch.setattr(run_evals_cli_modes, "build_llm_judge", lambda *arguments: None)
    monkeypatch.setattr(run_evals_cli_modes, "load_calibration_cases", lambda: [])
    monkeypatch.setattr(
        run_evals_cli_modes,
        "judge_agreement",
        lambda *arguments, **options: next(passes),
    )
    monkeypatch.setattr(
        run_evals_cli_modes, "print_calibration_summary", lambda agreement: True
    )
    monkeypatch.setattr(
        run_evals_cli_modes, "collect_and_print_provider_usage", lambda: {}
    )

    exit_code = run_evals_cli_modes.run_judge_calibration({}, arguments)

    output = capsys.readouterr().out
    assert "Verdict flips across 2 passes: 1/2 (b)" in output
    assert exit_code == 0
