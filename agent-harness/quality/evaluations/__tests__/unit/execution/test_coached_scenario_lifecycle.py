from unittest.mock import Mock

import pytest

from e2e.coaching import coached_scenario_runner as runner


@pytest.fixture
def coached_environment(monkeypatch, tmp_path):
    scenario = tmp_path / "scenario.yaml"
    scenario.write_text("name: improve naming\nprompt: rename variable\ntimeout: 7\n")
    parent = tmp_path / "workspaces"
    monkeypatch.setattr(runner, "E2E_WORKSPACE_PARENT", parent)
    replacements = {
        "herdr_server_is_reachable": Mock(return_value=True),
        "setup_workspace": Mock(),
        "create_isolated_herdr_tab_for_test": Mock(
            return_value={"pane_id": "pane", "tab_id": "tab"}
        ),
        "destroy_test_tab": Mock(),
        "launch_agent_in_herdr_pane": Mock(),
        "wait_for_agent_to_become_ready": Mock(return_value=True),
        "send_prompt_to_agent_session": Mock(return_value=True),
        "capture_visible_screen": Mock(return_value="screen"),
        "wait_for_response_completion": Mock(return_value=True),
        "capture_full_terminal_output": Mock(
            side_effect=[
                "● Read(file)\n● Update(file)",
                "● Read(file)\n● Read(other)\n● Update(file)",
            ]
        ),
        "calculate_nps_from_tool_sequence_and_workspace": Mock(side_effect=[60, 85]),
        "load_compliance_skill_body": Mock(return_value="policy"),
        "review_tool_sequence_for_compliance": Mock(
            side_effect=["FAIL: naming", "PASS: naming"]
        ),
    }
    for name, replacement in replacements.items():
        monkeypatch.setattr(runner, name, replacement)
    return scenario, parent, replacements


def test_coaching_applies_penalty_correction_and_always_cleans_up(coached_environment):
    scenario, parent, ports = coached_environment
    result = runner.run_coached_scenario(scenario, model="test-model")
    assert (result.initial_nps, result.coached_nps, result.improvement) == (45, 85, 40)
    assert result.initial_tool_sequence == ["Read", "Edit"]
    assert result.coached_tool_sequence == ["Read", "Read", "Edit"]
    assert "AFTER CORRECTION" in result.coach_findings and result.error is None
    prompts = ports["send_prompt_to_agent_session"].call_args_list
    assert prompts[0].args == ("pane", "rename variable")
    assert "FAIL: naming" in prompts[1].args[1]
    assert ports["wait_for_response_completion"].call_args.args == ("pane", "screen", 7)
    assert ports["launch_agent_in_herdr_pane"].call_args.args[2] == "test-model"
    ports["destroy_test_tab"].assert_called_once_with("tab")
    assert list(parent.iterdir()) == []


def test_passing_review_needs_no_correction(coached_environment):
    scenario, _, ports = coached_environment
    ports["review_tool_sequence_for_compliance"].side_effect = ["PASS: naming"]
    result = runner.run_coached_scenario(scenario)
    assert result.initial_nps == 60 and result.coached_nps == 85
    assert ports["send_prompt_to_agent_session"].call_count == 1
    assert ports["review_tool_sequence_for_compliance"].call_count == 1


@pytest.mark.parametrize(
    "port,error",
    [
        ("wait_for_agent_to_become_ready", "Worker failed to start"),
        ("send_prompt_to_agent_session", "Worker never completed the initial prompt"),
        ("wait_for_response_completion", "Worker never completed the initial prompt"),
    ],
)
def test_worker_failures_release_tab_and_workspace(coached_environment, port, error):
    scenario, parent, ports = coached_environment
    ports[port].return_value = False
    result = runner.run_coached_scenario(scenario)
    assert result.error == error and result.initial_nps == 0
    ports["destroy_test_tab"].assert_called_once_with("tab")
    ports["review_tool_sequence_for_compliance"].assert_not_called()
    assert list(parent.iterdir()) == []


def test_unreachable_server_allocates_nothing(coached_environment):
    scenario, parent, ports = coached_environment
    ports["herdr_server_is_reachable"].return_value = False
    assert runner.run_coached_scenario(scenario).error == "herdr server not reachable"
    assert not parent.exists()
    ports["create_isolated_herdr_tab_for_test"].assert_not_called()


def test_tab_creation_failure_cleans_workspace_without_destroying_unknown_tab(
    coached_environment,
):
    scenario, parent, ports = coached_environment
    ports["create_isolated_herdr_tab_for_test"].return_value = {}
    with pytest.raises(RuntimeError, match="could not be created"):
        runner.run_coached_scenario(scenario)
    ports["destroy_test_tab"].assert_not_called()
    assert list(parent.iterdir()) == []
