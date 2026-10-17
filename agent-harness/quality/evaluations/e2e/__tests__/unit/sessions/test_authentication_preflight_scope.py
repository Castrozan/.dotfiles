from pathlib import Path

import pytest

from e2e import e2e_scenario_runner


@pytest.mark.parametrize("harness_name", ["codex", "opencode"])
def test_non_claude_scenarios_do_not_require_claude_authentication(
    monkeypatch, tmp_path, harness_name
):
    monkeypatch.setattr(
        e2e_scenario_runner,
        "load_scenario",
        lambda path: {"name": "scenario", "harness": harness_name},
    )

    def unexpected_authentication_probe(*arguments):
        pytest.fail("Claude authentication must not gate another harness")

    monkeypatch.setattr(
        e2e_scenario_runner,
        "claude_authentication_failure",
        unexpected_authentication_probe,
    )
    expected_result = object()
    monkeypatch.setattr(e2e_scenario_runner, "E2E_WORKSPACE_PARENT", tmp_path)
    monkeypatch.setattr(e2e_scenario_runner, "herdr_server_is_reachable", lambda: True)
    monkeypatch.setattr(
        e2e_scenario_runner, "setup_e2e_scenario_workspace", lambda *arguments: None
    )
    monkeypatch.setattr(
        e2e_scenario_runner,
        "create_isolated_herdr_tab_for_test",
        lambda *arguments: {"tab_id": "tab", "pane_id": "pane"},
    )
    monkeypatch.setattr(
        e2e_scenario_runner, "launch_agent_in_herdr_pane", lambda *arguments: None
    )
    monkeypatch.setattr(
        e2e_scenario_runner, "wait_for_agent_to_become_ready", lambda *arguments: True
    )
    monkeypatch.setattr(
        e2e_scenario_runner, "destroy_test_tab", lambda *arguments: None
    )
    monkeypatch.setattr(
        e2e_scenario_runner, "_run_e2e_session", lambda *arguments: expected_result
    )

    assert (
        e2e_scenario_runner.run_e2e_scenario(Path("scenario.yaml")) is expected_result
    )


def test_dry_run_does_not_probe_authentication(monkeypatch):
    monkeypatch.setattr(
        e2e_scenario_runner, "load_scenario", lambda path: {"name": "scenario"}
    )

    def unexpected_authentication_probe(*arguments):
        pytest.fail("A dry run must not invoke Claude")

    monkeypatch.setattr(
        e2e_scenario_runner,
        "claude_authentication_failure",
        unexpected_authentication_probe,
    )

    assert e2e_scenario_runner.run_e2e_scenario(
        Path("scenario.yaml"), dry_run=True
    ).passed
