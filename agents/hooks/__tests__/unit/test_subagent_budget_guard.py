import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hook_module_loader import import_hyphenated_hook_module

subagent_budget_guard_handler = import_hyphenated_hook_module(
    "subagent_budget_guard_handler"
)
subagent_spawn_budget_state = import_hyphenated_hook_module(
    "subagent_spawn_budget_state"
)

INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE = "CLAUDE_INTERACTIVE_PREFERENCES_PATH"
CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER = "CLAWDE_AGENT_NAME"


@pytest.fixture
def interactive_session_with_isolated_state(monkeypatch, tmp_path):
    monkeypatch.setenv(
        INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE,
        "/nix/store/interactive-preferences.md",
    )
    monkeypatch.delenv(CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER, raising=False)
    monkeypatch.setenv(
        subagent_spawn_budget_state.STATE_DIRECTORY_OVERRIDE_ENVIRONMENT_VARIABLE,
        str(tmp_path),
    )
    return tmp_path


def spawn_hook_input(description="explore the module", session_id="session-under-test"):
    return {
        "tool_name": "Agent",
        "session_id": session_id,
        "tool_input": {"description": description, "prompt": "do the work"},
    }


def test_allows_the_spawns_below_the_ceiling(interactive_session_with_isolated_state):
    assert subagent_budget_guard_handler.handle(spawn_hook_input()) is None
    assert subagent_budget_guard_handler.handle(spawn_hook_input()) is None


def test_denies_the_spawn_that_passes_the_ceiling_without_a_declaration(
    interactive_session_with_isolated_state,
):
    subagent_budget_guard_handler.handle(spawn_hook_input())
    subagent_budget_guard_handler.handle(spawn_hook_input())
    result = subagent_budget_guard_handler.handle(spawn_hook_input())
    assert result is not None
    assert result.decision == "deny"
    assert "orchestrated:" in result.system_message


def test_a_denied_spawn_does_not_count_against_the_budget(
    interactive_session_with_isolated_state,
):
    for _ in range(4):
        subagent_budget_guard_handler.handle(spawn_hook_input())
    state = subagent_spawn_budget_state.read_subagent_spawn_budget_state(
        "session-under-test"
    )
    assert state[subagent_spawn_budget_state.ALLOWED_SPAWN_COUNT_KEY] == 2


def test_an_orchestrated_declaration_unlocks_the_rest_of_the_session(
    interactive_session_with_isolated_state,
):
    subagent_budget_guard_handler.handle(spawn_hook_input())
    subagent_budget_guard_handler.handle(spawn_hook_input())
    declared = subagent_budget_guard_handler.handle(
        spawn_hook_input(description="orchestrated: nine files across three modules")
    )
    assert declared is None
    assert subagent_budget_guard_handler.handle(spawn_hook_input()) is None


def test_ignores_tool_calls_that_are_not_a_subagent_spawn(
    interactive_session_with_isolated_state,
):
    assert (
        subagent_budget_guard_handler.handle(
            {"tool_name": "Bash", "tool_input": {"command": "echo orchestrated"}}
        )
        is None
    )


def test_does_not_hold_the_ceiling_for_a_background_clawde_agent(monkeypatch, tmp_path):
    monkeypatch.setenv(
        INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE,
        "/nix/store/interactive-preferences.md",
    )
    monkeypatch.setenv(CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER, "golden")
    monkeypatch.setenv(
        subagent_spawn_budget_state.STATE_DIRECTORY_OVERRIDE_ENVIRONMENT_VARIABLE,
        str(tmp_path),
    )
    for _ in range(5):
        assert subagent_budget_guard_handler.handle(spawn_hook_input()) is None


def test_does_not_hold_the_ceiling_outside_an_interactive_session(
    monkeypatch, tmp_path
):
    monkeypatch.delenv(INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE, raising=False)
    monkeypatch.delenv(CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER, raising=False)
    monkeypatch.setenv(
        subagent_spawn_budget_state.STATE_DIRECTORY_OVERRIDE_ENVIRONMENT_VARIABLE,
        str(tmp_path),
    )
    for _ in range(5):
        assert subagent_budget_guard_handler.handle(spawn_hook_input()) is None


def test_separate_sessions_hold_separate_budgets(
    interactive_session_with_isolated_state,
):
    subagent_budget_guard_handler.handle(spawn_hook_input(session_id="first-session"))
    subagent_budget_guard_handler.handle(spawn_hook_input(session_id="first-session"))
    assert (
        subagent_budget_guard_handler.handle(
            spawn_hook_input(session_id="first-session")
        )
        is not None
    )
    assert (
        subagent_budget_guard_handler.handle(
            spawn_hook_input(session_id="second-session")
        )
        is None
    )


def test_a_corrupt_state_file_falls_back_to_an_empty_budget(
    interactive_session_with_isolated_state,
):
    subagent_spawn_budget_state.subagent_spawn_budget_state_path(
        "session-under-test"
    ).write_text("not json")
    assert subagent_budget_guard_handler.handle(spawn_hook_input()) is None
