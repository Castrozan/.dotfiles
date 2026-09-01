from types import SimpleNamespace

import run_evals_cli_modes


def test_judge_calibration_honors_the_requested_worker_limit(monkeypatch):
    observed = {}
    arguments = SimpleNamespace(judge_harness="codex", workers=1)
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
