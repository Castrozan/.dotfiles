import json
from datetime import datetime, timezone

import run_evals_baseline

EXPECTED_PROFILE = {
    "subject": {
        "harness": "codex",
        "model": "gpt-5.6-sol",
        "reasoning_effort": "medium",
    },
    "judge": {
        "harness": "codex",
        "model": "gpt-5.6-luna",
        "reasoning_effort": "low",
    },
}


def test_baseline_check_compares_against_the_configured_execution_profile(
    tmp_path, monkeypatch
):
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "git_commit": "abc",
                "total_tests": 1,
                "total_passed": 1,
                "pass_rate": 1.0,
                "categories": {},
                "execution_profile": {"subject": {"harness": "claude"}},
            }
        )
    )
    observed = {}

    def evidence_failures(*arguments):
        observed["expected"] = arguments[-1]
        return ["profile mismatch"]

    monkeypatch.setattr(run_evals_baseline, "BASELINE_PATH", baseline_path)
    monkeypatch.setattr(
        run_evals_baseline, "baseline_evidence_failures", evidence_failures
    )
    monkeypatch.setattr(
        run_evals_baseline,
        "previous_committed_baseline_pass_rate",
        lambda profile: None,
    )

    passed = run_evals_baseline.check_baseline_for_regression(
        EXPECTED_PROFILE, {"tests": {}}
    )

    assert passed is False
    assert observed["expected"] == EXPECTED_PROFILE
