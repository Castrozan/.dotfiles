import json

import pytest

import run_evals_ab_record
from run_evals_ab_record import save_ab_profile

EXECUTION_PROFILE = {
    "subject": {"harness": "claude", "model": "sonnet", "reasoning_effort": "high"},
    "judge": {"harness": "claude", "model": "opus", "reasoning_effort": None},
}
TOKEN_USAGE = {"input_tokens": 100, "output_tokens": 50}


def valid_comparison():
    return {
        "method": "paired_hierarchical_bootstrap",
        "epochs": 3,
        "n_paired": 21,
        "sample_pairs": 63,
        "variant_a_pass_rate": 0.95,
        "variant_b_pass_rate": 0.93,
        "delta": 0.02,
        "lower_bound": -0.05,
        "upper_bound": 0.09,
        "candidate_hard_failures": [],
        "candidate_case_outcomes": {
            "skills/humanize/reader_recovery::recovery": [True, True, False]
        },
    }


def test_ab_profile_requires_repeated_absolute_and_control_gates(tmp_path, monkeypatch):
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text("{}")
    monkeypatch.setattr(run_evals_ab_record, "BASELINE_PATH", baseline_path)

    for field, value, message in (
        ("method", "mcnemar_exact", "repeated sampling"),
        ("variant_a_pass_rate", 0.89, "at least 90%"),
        ("delta", -0.01, "must not trail"),
        ("candidate_hard_failures", ["case"], "hard-failed"),
    ):
        comparison = valid_comparison()
        comparison[field] = value
        with pytest.raises(ValueError, match=message):
            save_ab_profile(
                comparison,
                "skills/humanize/reader_recovery",
                "base",
                EXECUTION_PROFILE,
                TOKEN_USAGE,
            )


def test_ab_profile_records_scoped_fingerprints(tmp_path, monkeypatch):
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text("{}")
    monkeypatch.setattr(run_evals_ab_record, "BASELINE_PATH", baseline_path)
    monkeypatch.setattr(
        run_evals_ab_record,
        "humanize_recovery_fingerprints",
        lambda: {"suite": "recovery", "instructions": "humanize"},
    )
    monkeypatch.setattr(
        run_evals_ab_record,
        "merge_baseline_categories",
        lambda baseline, replacements, execution_profile, token_usage: baseline
        | {"categories": replacements},
    )

    save_ab_profile(
        valid_comparison(),
        "skills/humanize/reader_recovery",
        "pre-change",
        EXECUTION_PROFILE,
        TOKEN_USAGE,
    )

    profile = json.loads(baseline_path.read_text())["evidence_profiles"][
        "skills/humanize/reader_recovery"
    ]
    assert profile["comparison_ref"] == "pre-change"
    assert profile["candidate_pass_rate"] == 0.95
    assert profile["candidate_cases"]["recovery"] == {"passes": 2, "samples": 3}
    assert profile["fingerprints"] == {
        "suite": "recovery",
        "instructions": "humanize",
    }
    assert profile["execution_profile"] == EXECUTION_PROFILE
    assert profile["token_usage"] == TOKEN_USAGE
