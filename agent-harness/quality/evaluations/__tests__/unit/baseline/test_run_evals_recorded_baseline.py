import json
from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from runner.baseline import run_evals_baseline, run_evals_recorded_baseline
from runner.baseline.run_evals_impact import evaluation_test_fingerprints
from runner.run_evals_execution_profile import execution_profile_identifier


EXECUTION_PROFILE = {
    "subject": {"harness": "codex", "model": "subject", "reasoning_effort": "high"},
    "judge": {"harness": "codex", "model": "judge", "reasoning_effort": "high"},
}


@pytest.fixture
def recorded_scenario(tmp_path, monkeypatch):
    config = {
        "settings": {
            "canonical_subject_harness": "codex",
            "canonical_judge_harness": "codex",
            "subject_models": {"codex": "subject"},
            "judge_models": {"codex": "judge"},
            "subject_reasoning_efforts": {"codex": "high"},
            "judge_reasoning_efforts": {"codex": "high"},
        },
        "tests": {
            "communication": [
                {
                    "name": "recorded_case",
                    "prompt": "Original measured prompt",
                    "system_prompt": "Original instruction",
                    "assertions": {"output_contains": ["answer"]},
                }
            ]
        },
    }
    fingerprint = evaluation_test_fingerprints(config)["communication::recorded_case"]
    profile_identifier = execution_profile_identifier(EXECUTION_PROFILE)
    baseline = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_tests": 1,
        "total_passed": 1,
        "total_failed": 0,
        "pass_rate": 1.0,
        "minimum_current_evidence": 1,
        "execution_profile": EXECUTION_PROFILE,
        "execution_profiles": {profile_identifier: EXECUTION_PROFILE},
        "categories": {
            "communication": {
                "passed": 1,
                "failed": 0,
                "tests": [
                    {
                        "name": "recorded_case",
                        "passed": True,
                        "fingerprint": fingerprint,
                    }
                ],
            }
        },
    }
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps(baseline))
    for module in (run_evals_baseline, run_evals_recorded_baseline):
        monkeypatch.setattr(module, "BASELINE_PATH", baseline_path)
        monkeypatch.setattr(
            module, "previous_committed_baseline_pass_rate", lambda profile: None
        )
    return SimpleNamespace(config=config, baseline=baseline, path=baseline_path)


def test_changed_model_input_is_reported_without_blocking_recorded_result_check(
    recorded_scenario, capsys
):
    scenario = recorded_scenario
    scenario.config["tests"]["communication"][0]["prompt"] = "Changed prompt"
    baseline_bytes = scenario.path.read_bytes()

    assert run_evals_recorded_baseline.check_recorded_baseline(
        EXECUTION_PROFILE, scenario.config
    )
    report = capsys.readouterr().out

    assert "0/1 tests" in report
    assert "Pending evidence: 1 stale, 0 missing" in report
    assert "Stale evidence: communication::recorded_case" in report
    assert "Current model behavior was not measured" in report
    assert scenario.path.read_bytes() == baseline_bytes
    assert not run_evals_baseline.check_baseline_for_regression(
        EXECUTION_PROFILE, scenario.config
    )


def test_old_measurements_are_reported_without_claiming_freshness(
    recorded_scenario, capsys
):
    scenario = recorded_scenario
    scenario.baseline["generated_at"] = "2000-01-01T00:00:00+00:00"
    scenario.path.write_text(json.dumps(scenario.baseline))

    assert run_evals_recorded_baseline.check_recorded_baseline(
        EXECUTION_PROFILE, scenario.config
    )
    assert "Measurement refresh required:" in capsys.readouterr().out


@pytest.mark.parametrize(
    "corruption",
    ("aggregate", "duplicate", "outcome", "coverage", "profile"),
)
def test_recorded_check_rejects_false_or_insufficient_evidence(
    corruption, recorded_scenario
):
    scenario = recorded_scenario
    bucket = scenario.baseline["categories"]["communication"]
    changes = {
        "aggregate": lambda: scenario.baseline.update(total_passed=100),
        "duplicate": lambda: bucket["tests"].append(deepcopy(bucket["tests"][0])),
        "outcome": lambda: bucket["tests"][0].update(passed="false"),
        "coverage": lambda: scenario.baseline.update(minimum_current_evidence=2),
        "profile": lambda: scenario.baseline.update(execution_profile={}),
    }
    changes[corruption]()
    scenario.path.write_text(json.dumps(scenario.baseline))

    assert not run_evals_recorded_baseline.check_recorded_baseline(
        EXECUTION_PROFILE, scenario.config
    )


def test_recorded_check_keeps_pass_rate_and_regression_failures(
    recorded_scenario, monkeypatch, capsys
):
    scenario = recorded_scenario
    scenario.baseline["categories"]["communication"]["tests"][0]["passed"] = False
    scenario.baseline["categories"]["communication"].update(passed=0, failed=1)
    scenario.baseline.update(total_passed=0, total_failed=1, pass_rate=0.0)
    scenario.path.write_text(json.dumps(scenario.baseline))
    monkeypatch.setattr(
        run_evals_recorded_baseline,
        "previous_committed_baseline_pass_rate",
        lambda profile: 1.0,
    )

    assert not run_evals_recorded_baseline.check_recorded_baseline(
        EXECUTION_PROFILE, scenario.config
    )
    report = capsys.readouterr().out
    assert "Overall pass rate" in report
    assert "Communication pass rate" in report
    assert "max allowed drop 5.0%" in report


def test_recorded_check_rejects_invalid_current_evaluation_contract(
    recorded_scenario, capsys
):
    scenario = recorded_scenario
    scenario.config["tests"]["communication"][0]["prompt"] = ""

    assert not run_evals_recorded_baseline.check_recorded_baseline(
        EXECUTION_PROFILE, scenario.config
    )
    assert "missing prompt" in capsys.readouterr().out
