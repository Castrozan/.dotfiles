import pytest
from workflow_budget_test_support import (
    COUNTING_WORKFLOW_SCRIPT,
    INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE,
    SESSION_UNDER_TEST,
    agent_hook_input,
    guarded_script_of,
    interactive_session_with_isolated_state,
    subagent_budget_guard_handler,
    subagent_spawn_budget_state,
    workflow_budget_guard_handler,
    workflow_hook_input,
    workflow_script_budget_prelude,
)

__all__ = ["interactive_session_with_isolated_state"]


def test_ignores_every_tool_other_than_workflow(
    interactive_session_with_isolated_state,
):
    assert workflow_budget_guard_handler.handle(agent_hook_input()) is None


def test_rewrites_the_script_without_deciding_its_permission(
    interactive_session_with_isolated_state,
):
    result = workflow_budget_guard_handler.handle(
        workflow_hook_input({"script": COUNTING_WORKFLOW_SCRIPT})
    )
    assert workflow_script_budget_prelude.PRELUDE_START_MARKER in guarded_script_of(
        result
    )
    assert "2 agent() calls" in result.additional_context


def test_spends_the_remaining_light_tier_allowance_and_then_refuses(
    interactive_session_with_isolated_state,
):
    assert subagent_budget_guard_handler.handle(agent_hook_input()) is None
    first_workflow = workflow_budget_guard_handler.handle(
        workflow_hook_input({"script": COUNTING_WORKFLOW_SCRIPT})
    )
    assert "1 agent() calls" in first_workflow.additional_context
    second_workflow = workflow_budget_guard_handler.handle(
        workflow_hook_input({"script": COUNTING_WORKFLOW_SCRIPT})
    )
    assert second_workflow.decision == "deny"
    assert "orchestrated:" in second_workflow.system_message
    assert subagent_budget_guard_handler.handle(agent_hook_input()).decision == "deny"


def test_an_orchestrated_declaration_raises_the_ceiling(
    interactive_session_with_isolated_state,
):
    result = workflow_budget_guard_handler.handle(
        workflow_hook_input(
            {
                "script": COUNTING_WORKFLOW_SCRIPT,
                "description": "orchestrated: audit spans more than two modules",
            }
        )
    )
    assert "32 agent() calls" in result.additional_context
    assert "400000 Opus-equivalent output tokens" in result.additional_context
    assert result.updated_input["description"].startswith("orchestrated:")


def test_non_interactive_runs_get_the_orchestrated_ceiling(monkeypatch, tmp_path):
    monkeypatch.delenv(INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE, raising=False)
    monkeypatch.setenv(
        subagent_spawn_budget_state.STATE_DIRECTORY_OVERRIDE_ENVIRONMENT_VARIABLE,
        str(tmp_path),
    )
    result = workflow_budget_guard_handler.handle(
        workflow_hook_input({"script": COUNTING_WORKFLOW_SCRIPT})
    )
    assert "32 agent() calls" in result.additional_context


def test_inlines_a_script_path_and_keeps_the_resume_id(
    interactive_session_with_isolated_state,
):
    script_path = interactive_session_with_isolated_state / "counting.js"
    script_path.write_text(COUNTING_WORKFLOW_SCRIPT)
    result = workflow_budget_guard_handler.handle(
        workflow_hook_input(
            {"scriptPath": str(script_path), "resumeFromRunId": "wf_abcdef1"}
        )
    )
    assert result.updated_input["resumeFromRunId"] == "wf_abcdef1"
    assert "scriptPath" not in result.updated_input
    assert (
        workflow_script_budget_prelude.PRELUDE_START_MARKER
        in (result.updated_input["script"])
    )


def test_inlines_a_saved_workflow_found_by_name(
    interactive_session_with_isolated_state,
):
    project_directory = interactive_session_with_isolated_state / "project"
    saved_workflows = project_directory / ".claude" / "workflows"
    saved_workflows.mkdir(parents=True)
    (saved_workflows / "counting.js").write_text(COUNTING_WORKFLOW_SCRIPT)
    result = workflow_budget_guard_handler.handle(
        workflow_hook_input({"name": "counting"}, project_directory)
    )
    assert "name" not in result.updated_input
    assert result.updated_input["script"].startswith("export const meta")


def test_refuses_a_workflow_it_cannot_read(interactive_session_with_isolated_state):
    result = workflow_budget_guard_handler.handle(
        workflow_hook_input({"name": "no-such-workflow"})
    )
    assert result.decision == "deny"


@pytest.mark.parametrize(
    "bypassing_line",
    [
        "await globalThis.agent('x');",
        "await eval('agent')('x');",
        "await Function('return this')().agent('x');",
        "await workflow('child');",
    ],
)
def test_refuses_constructs_that_reach_around_the_ceiling(
    interactive_session_with_isolated_state, bypassing_line
):
    result = workflow_budget_guard_handler.handle(
        workflow_hook_input({"script": COUNTING_WORKFLOW_SCRIPT + bypassing_line})
    )
    assert result.decision == "deny"
    state = subagent_spawn_budget_state.read_subagent_spawn_budget_state(
        SESSION_UNDER_TEST
    )
    assert state[subagent_spawn_budget_state.ALLOWED_SPAWN_COUNT_KEY] == 0


def test_refuses_a_script_without_meta_and_spends_no_allowance(
    interactive_session_with_isolated_state,
):
    result = workflow_budget_guard_handler.handle(
        workflow_hook_input({"script": "return await agent('x');"})
    )
    assert result.decision == "deny"
    assert subagent_budget_guard_handler.handle(agent_hook_input()) is None
