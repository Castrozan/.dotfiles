from pathlib import Path

import e2e_herdr_io
import e2e_scenario_steps
from e2e_scenario_steps import (
    run_scenario_step,
    scenario_steps,
    step_requests_compaction,
)
from e2e_workspace import SCENARIOS_DIR, load_scenario


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


def test_a_compaction_step_fails_the_scenario_when_compaction_is_refused(monkeypatch):
    monkeypatch.setattr(
        e2e_scenario_steps,
        "compact_claude_session",
        lambda pane_id, timeout_seconds: False,
    )
    failure = run_scenario_step("pane", {"compact": True}, 5)
    assert failure == "session compaction was refused or never confirmed"


def test_a_compaction_step_passes_when_compaction_is_confirmed(monkeypatch):
    monkeypatch.setattr(
        e2e_scenario_steps,
        "compact_claude_session",
        lambda pane_id, timeout_seconds: True,
    )
    assert run_scenario_step("pane", {"compact": True}, 5) is None


def test_compaction_is_refused_when_the_pane_reports_too_few_messages(monkeypatch):
    monkeypatch.setattr(
        e2e_herdr_io, "send_prompt_to_claude_session", lambda pane_id, prompt_text: True
    )
    monkeypatch.setattr(
        e2e_herdr_io,
        "wait_for_response_completion",
        lambda pane_id, output_after_send, timeout_seconds: True,
    )
    monkeypatch.setattr(
        e2e_herdr_io,
        "capture_full_terminal_output",
        lambda pane_id: "Not enough messages to compact",
    )
    assert e2e_herdr_io.compact_claude_session("pane", timeout_seconds=5) is False


def test_compaction_is_confirmed_only_by_the_compacted_marker(monkeypatch):
    monkeypatch.setattr(
        e2e_herdr_io, "send_prompt_to_claude_session", lambda pane_id, prompt_text: True
    )
    monkeypatch.setattr(
        e2e_herdr_io,
        "wait_for_response_completion",
        lambda pane_id, output_after_send, timeout_seconds: True,
    )
    monkeypatch.setattr(
        e2e_herdr_io,
        "capture_full_terminal_output",
        lambda pane_id: "Compacted (ctrl+o to see full summary)",
    )
    assert e2e_herdr_io.compact_claude_session("pane", timeout_seconds=5) is True


def test_the_compaction_scenario_compacts_before_its_unprompted_coding_request():
    scenario = load_scenario(
        Path(SCENARIOS_DIR) / "no-comments-survives-compaction.yaml"
    )
    steps = scenario_steps(scenario)
    compaction_positions = [
        index for index, step in enumerate(steps) if step_requests_compaction(step)
    ]
    assert len(compaction_positions) == 1
    compaction_index = compaction_positions[0]
    assert compaction_index >= 5
    assert compaction_index < len(steps) - 1
    final_request = steps[-1]
    assert "comment" not in final_request.lower()
    assert "docstring" not in final_request.lower()
