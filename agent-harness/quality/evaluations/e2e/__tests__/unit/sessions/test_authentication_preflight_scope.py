from pathlib import Path

import pytest

from e2e import e2e_scenario_runner


@pytest.mark.parametrize("harness_name", ["codex", "opencode"])
def test_non_claude_scenarios_do_not_require_claude_authentication(
    monkeypatch, harness_name
):
    monkeypatch.setattr(
        e2e_scenario_runner,
        "load_scenario",
        lambda path: {"name": "scenario", "harness": harness_name},
    )

    def unexpected_authentication_probe():
        pytest.fail("Claude authentication must not gate another harness")

    monkeypatch.setattr(
        e2e_scenario_runner,
        "claude_authentication_failure",
        unexpected_authentication_probe,
    )
    expected_result = object()
    monkeypatch.setattr(
        e2e_scenario_runner, "_run_live_scenario", lambda *arguments: expected_result
    )

    assert (
        e2e_scenario_runner.run_e2e_scenario(Path("scenario.yaml")) is expected_result
    )


def test_dry_run_does_not_probe_authentication(monkeypatch):
    monkeypatch.setattr(
        e2e_scenario_runner, "load_scenario", lambda path: {"name": "scenario"}
    )

    def unexpected_authentication_probe():
        pytest.fail("A dry run must not invoke Claude")

    monkeypatch.setattr(
        e2e_scenario_runner,
        "claude_authentication_failure",
        unexpected_authentication_probe,
    )

    assert e2e_scenario_runner.run_e2e_scenario(
        Path("scenario.yaml"), dry_run=True
    ).passed
