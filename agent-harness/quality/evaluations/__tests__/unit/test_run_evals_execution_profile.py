import pytest

import run_evals_baseline_record
from run_evals_baseline_policy import (
    REQUIRED_HUMANIZE_PROFILE,
    baseline_evidence_failures,
    preserved_evidence_profiles,
)
from run_evals_baseline_record import merge_baseline_categories
from run_evals_execution_profile import build_execution_profile

EXECUTION_PROFILE = {
    "subject": {"harness": "claude", "model": "sonnet", "reasoning_effort": "high"},
    "judge": {"harness": "claude", "model": "opus", "reasoning_effort": None},
}
OTHER_EXECUTION_PROFILE = {
    "subject": {"harness": "codex", "model": "o4", "reasoning_effort": None},
    "judge": {"harness": "claude", "model": "opus", "reasoning_effort": None},
}
TOKEN_USAGE = {"input_tokens": 100, "output_tokens": 50}
FINGERPRINTS = {"suite": "s", "instructions": "i"}


def test_build_execution_profile_from_required_and_optional_settings():
    settings = {
        "subject_models": {"claude": "sonnet", "codex": "o4"},
        "judge_models": {"claude": "opus"},
        "subject_reasoning_efforts": {"claude": "high"},
    }
    profile = build_execution_profile(settings, "claude", "claude")
    assert profile == {
        "subject": {"harness": "claude", "model": "sonnet", "reasoning_effort": "high"},
        "judge": {"harness": "claude", "model": "opus", "reasoning_effort": None},
    }


def test_build_execution_profile_omits_reasoning_effort_when_unconfigured():
    settings = {
        "subject_models": {"codex": "o4"},
        "judge_models": {"claude": "opus"},
    }
    profile = build_execution_profile(settings, "codex", "claude")
    assert profile["subject"]["reasoning_effort"] is None
    assert profile["judge"]["reasoning_effort"] is None


def test_category_merge_writes_execution_profile_and_token_usage(monkeypatch):
    monkeypatch.setattr(
        run_evals_baseline_record,
        "evaluation_category_names",
        lambda: {"communication"},
    )
    baseline = {}
    merged = merge_baseline_categories(
        baseline,
        {"communication": {"passed": 3, "failed": 0, "tests": []}},
        EXECUTION_PROFILE,
        TOKEN_USAGE,
    )
    assert merged["execution_profile"] == EXECUTION_PROFILE
    assert merged["token_usage"] == TOKEN_USAGE


def test_category_merge_rejects_a_mismatched_or_missing_existing_profile():
    replacement = {"passed": 3, "failed": 0, "tests": []}
    for baseline in (
        {"execution_profile": OTHER_EXECUTION_PROFILE, "categories": {}},
        {"categories": {}},
    ):
        with pytest.raises(ValueError, match="execution profile"):
            merge_baseline_categories(
                baseline, {"communication": replacement}, EXECUTION_PROFILE, TOKEN_USAGE
            )


def test_evidence_profile_preserved_only_for_an_exact_execution_profile_match():
    baseline = {
        "evidence_profiles": {
            "a": {"fingerprints": FINGERPRINTS, "execution_profile": EXECUTION_PROFILE},
            "b": {
                "fingerprints": FINGERPRINTS,
                "execution_profile": OTHER_EXECUTION_PROFILE,
            },
            "c": {"fingerprints": FINGERPRINTS},
        }
    }
    preserved = preserved_evidence_profiles(baseline, FINGERPRINTS, EXECUTION_PROFILE)
    assert set(preserved) == {"a"}


def test_baseline_policy_rejects_a_mismatched_execution_profile():
    baseline = {
        "categories": {},
        "execution_profile": EXECUTION_PROFILE,
        "evidence_profiles": {
            REQUIRED_HUMANIZE_PROFILE: {
                "epochs": 3,
                "candidate_pass_rate": 0.95,
                "delta": 0.05,
                "candidate_hard_failures": [],
                "fingerprints": FINGERPRINTS,
                "execution_profile": EXECUTION_PROFILE,
            }
        },
    }
    failures = baseline_evidence_failures(
        baseline,
        FINGERPRINTS,
        FINGERPRINTS,
        set(baseline["categories"]),
        OTHER_EXECUTION_PROFILE,
    )
    assert any("execution profile" in failure for failure in failures)
