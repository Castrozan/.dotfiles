import e2e_herdr_io
import e2e_scenario_steps
from e2e_harness_profiles import CLAUDE_PROFILE, CODEX_PROFILE
from e2e_scenario_steps import (
    run_scenario_step,
    scenario_steps,
    step_requests_compaction,
)
from e2e_workspace import SCENARIOS_DIR, discover_scenario_files, load_scenario


def stub_compaction_pane(monkeypatch, terminal_output):
    monkeypatch.setattr(
        e2e_herdr_io,
        "send_prompt_to_agent_session",
        lambda pane_id, prompt_text: True,
    )
    monkeypatch.setattr(
        e2e_herdr_io,
        "wait_for_response_completion",
        lambda pane_id, output_after_send, timeout_seconds, busy_marker: True,
    )
    monkeypatch.setattr(
        e2e_herdr_io,
        "capture_visible_screen",
        lambda pane_id: terminal_output,
    )
    monkeypatch.setattr(
        e2e_herdr_io,
        "capture_screen_and_scrollback",
        lambda pane_id: terminal_output,
    )


def test_a_plain_string_step_is_a_prompt_and_a_compact_mapping_is_not():
    assert not step_requests_compaction("write the function")
    assert step_requests_compaction({"compact": True})
    assert not step_requests_compaction({"compact": False})


def test_scenario_steps_reads_the_prompts_list_then_falls_back_to_one_prompt():
    assert scenario_steps({"prompts": ["first", {"compact": True}]}) == [
        "first",
        {"compact": True},
    ]
    assert scenario_steps({"prompt": "only"}) == ["only"]
    assert scenario_steps({}) == []


def stub_live_agent(monkeypatch, pane_hosts_an_agent=True):
    monkeypatch.setattr(
        e2e_scenario_steps,
        "pane_hosts_a_live_agent",
        lambda pane_id: pane_hosts_an_agent,
    )


def test_a_step_fails_immediately_when_the_harness_session_has_exited(monkeypatch):
    stub_live_agent(monkeypatch, pane_hosts_an_agent=False)
    failure = run_scenario_step("pane", "write the function", CODEX_PROFILE, 5)
    assert failure == "the codex session is no longer running in the herdr pane"


def test_a_compaction_step_fails_the_scenario_when_compaction_is_refused(monkeypatch):
    stub_live_agent(monkeypatch)
    monkeypatch.setattr(
        e2e_scenario_steps,
        "compact_agent_session",
        lambda pane_id, profile, timeout_seconds: False,
    )
    failure = run_scenario_step("pane", {"compact": True}, CODEX_PROFILE, 5)
    assert failure == (
        "codex session compaction was never confirmed with 'Context compacted'"
    )
    stub_live_agent(monkeypatch)
    claude_failure = run_scenario_step("pane", {"compact": True}, CLAUDE_PROFILE, 5)
    assert "refused or never confirmed" in claude_failure


def test_a_compaction_step_passes_when_compaction_is_confirmed(monkeypatch):
    stub_live_agent(monkeypatch)
    monkeypatch.setattr(
        e2e_scenario_steps,
        "compact_agent_session",
        lambda pane_id, profile, timeout_seconds: True,
    )
    assert run_scenario_step("pane", {"compact": True}, CLAUDE_PROFILE, 5) is None


def test_compaction_is_refused_when_the_pane_reports_too_few_messages(monkeypatch):
    stub_compaction_pane(monkeypatch, "Not enough messages to compact")
    assert (
        e2e_herdr_io.compact_agent_session("pane", CLAUDE_PROFILE, timeout_seconds=5)
        is False
    )


def test_compaction_is_confirmed_only_by_the_profile_marker(monkeypatch):
    stub_compaction_pane(monkeypatch, "Compacted (ctrl+o to see full summary)")
    assert (
        e2e_herdr_io.compact_agent_session("pane", CLAUDE_PROFILE, timeout_seconds=5)
        is True
    )
    assert (
        e2e_herdr_io.compact_agent_session("pane", CODEX_PROFILE, timeout_seconds=5)
        is False
    )


def test_an_absent_refusal_marker_never_refuses_a_confirmed_compaction(monkeypatch):
    assert CODEX_PROFILE.compaction_refusal_marker == ""
    stub_compaction_pane(monkeypatch, "Context compacted")
    assert (
        e2e_herdr_io.compact_agent_session("pane", CODEX_PROFILE, timeout_seconds=5)
        is True
    )


def compaction_scenarios():
    return [
        scenario
        for scenario in map(load_scenario, discover_scenario_files(SCENARIOS_DIR))
        if any(step_requests_compaction(step) for step in scenario_steps(scenario))
    ]


def test_every_compaction_scenario_compacts_before_an_unprompted_coding_request():
    scenarios = compaction_scenarios()
    assert {scenario.get("harness", "claude") for scenario in scenarios} == {
        "claude",
        "codex",
    }
    for scenario in scenarios:
        steps = scenario_steps(scenario)
        compaction_positions = [
            index for index, step in enumerate(steps) if step_requests_compaction(step)
        ]
        assert len(compaction_positions) == 1, scenario["name"]
        compaction_index = compaction_positions[0]
        assert compaction_index >= 5, scenario["name"]
        assert compaction_index < len(steps) - 1, scenario["name"]
        final_request = steps[-1].lower()
        assert "comment" not in final_request, scenario["name"]
        assert "docstring" not in final_request, scenario["name"]
