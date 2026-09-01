import run_evals_baseline_history as history
from run_evals_baseline_history import (
    BASELINE_REPOSITORY_PATH,
    baseline_regression_failure,
    committed_baseline_pass_rates,
    previous_committed_baseline_pass_rate,
)

EXECUTION_PROFILE = {
    "subject": {"harness": "claude", "model": "sonnet", "reasoning_effort": "high"},
    "judge": {"harness": "claude", "model": "opus", "reasoning_effort": None},
}
OTHER_EXECUTION_PROFILE = {
    "subject": {"harness": "codex", "model": "o4", "reasoning_effort": None},
    "judge": {"harness": "claude", "model": "opus", "reasoning_effort": None},
}


def test_regression_failure_flags_a_drop_beyond_the_allowed_margin():
    message = baseline_regression_failure(0.85, 0.95, 0.05)
    assert message is not None
    assert "dropped" in message
    assert "85.0%" in message
    assert "95.0%" in message


def test_regression_failure_tolerates_a_drop_within_the_margin():
    assert baseline_regression_failure(0.93, 0.95, 0.05) is None


def test_regression_failure_ignores_an_improvement():
    assert baseline_regression_failure(0.99, 0.95, 0.05) is None


def test_regression_failure_is_silent_without_a_previous_baseline():
    assert baseline_regression_failure(0.10, None, 0.05) is None


def test_previous_pass_rate_is_the_second_most_recent(monkeypatch):
    monkeypatch.setattr(
        history, "committed_baseline_pass_rates", lambda profile: [0.90, 0.95, 0.80]
    )
    assert previous_committed_baseline_pass_rate(EXECUTION_PROFILE) == 0.95


def test_previous_pass_rate_needs_two_recorded_baselines(monkeypatch):
    monkeypatch.setattr(
        history, "committed_baseline_pass_rates", lambda profile: [0.90]
    )
    assert previous_committed_baseline_pass_rate(EXECUTION_PROFILE) is None
    monkeypatch.setattr(history, "committed_baseline_pass_rates", lambda profile: [])
    assert previous_committed_baseline_pass_rate(EXECUTION_PROFILE) is None


def test_committed_pass_rates_skips_missing_reset_and_malformed_baselines(monkeypatch):
    commits = [
        ("c1", "", BASELINE_REPOSITORY_PATH),
        ("c2", "", BASELINE_REPOSITORY_PATH),
        ("c3", "", BASELINE_REPOSITORY_PATH),
        ("c4", "", BASELINE_REPOSITORY_PATH),
        ("c5", "", BASELINE_REPOSITORY_PATH),
    ]
    baselines = {
        "c1": {
            "total_tests": 174,
            "pass_rate": 0.90,
            "execution_profile": EXECUTION_PROFILE,
        },
        "c2": None,
        "c3": {
            "total_tests": 1,
            "pass_rate": 0.10,
            "execution_profile": EXECUTION_PROFILE,
        },
        "c4": {
            "total_tests": 174,
            "pass_rate": "n/a",
            "execution_profile": EXECUTION_PROFILE,
        },
        "c5": {
            "total_tests": 166,
            "pass_rate": 0.95,
            "execution_profile": EXECUTION_PROFILE,
        },
    }
    monkeypatch.setattr(history, "commits_touching_baseline", lambda: iter(commits))
    monkeypatch.setattr(history, "baseline_at_commit", lambda sha, path: baselines[sha])
    assert committed_baseline_pass_rates(EXECUTION_PROFILE) == [0.90, 0.95]


def test_committed_pass_rates_ignore_baselines_with_another_execution_profile(
    monkeypatch,
):
    commits = [
        ("c1", "", BASELINE_REPOSITORY_PATH),
        ("c2", "", BASELINE_REPOSITORY_PATH),
        ("c3", "", BASELINE_REPOSITORY_PATH),
    ]
    baselines = {
        "c1": {
            "total_tests": 174,
            "pass_rate": 0.92,
            "execution_profile": EXECUTION_PROFILE,
        },
        "c2": {
            "total_tests": 174,
            "pass_rate": 0.80,
            "execution_profile": OTHER_EXECUTION_PROFILE,
        },
        "c3": {"total_tests": 174, "pass_rate": 0.70},
    }
    monkeypatch.setattr(history, "commits_touching_baseline", lambda: iter(commits))
    monkeypatch.setattr(history, "baseline_at_commit", lambda sha, path: baselines[sha])
    assert committed_baseline_pass_rates(EXECUTION_PROFILE) == [0.92]
