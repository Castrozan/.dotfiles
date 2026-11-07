import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from hook_module_loader import import_hyphenated_hook_module

subagent_budget_guard_handler = import_hyphenated_hook_module(
    "subagent_budget_guard_handler"
)
subagent_spawn_budget_state = import_hyphenated_hook_module(
    "subagent_spawn_budget_state"
)


@pytest.fixture
def interactive_session_with_isolated_state(monkeypatch, tmp_path):
    monkeypatch.setenv(
        "AGENT_INTERACTIVE_PREFERENCES_PATH", "/nix/store/interactive-communication.md"
    )
    monkeypatch.delenv("CLAWDE_AGENT_NAME", raising=False)
    monkeypatch.setenv(
        subagent_spawn_budget_state.STATE_DIRECTORY_OVERRIDE_ENVIRONMENT_VARIABLE,
        str(tmp_path),
    )


def spawn_of(subagent_type):
    return {
        "tool_name": "Agent",
        "session_id": "session-under-test",
        "tool_input": {
            "description": "sweep the repository",
            "prompt": "find every pin",
            "subagent_type": subagent_type,
        },
    }


@pytest.mark.parametrize("scout_type", ["dotfiles:explore", "explore", "Explore"])
def test_read_only_explore_scouts_never_count_against_the_ceiling(
    interactive_session_with_isolated_state, scout_type
):
    for _ in range(5):
        assert subagent_budget_guard_handler.handle(spawn_of(scout_type)) is None
    assert subagent_budget_guard_handler.handle(spawn_of("general-purpose")) is None
    assert subagent_budget_guard_handler.handle(spawn_of("general-purpose")) is None
    assert subagent_budget_guard_handler.handle(spawn_of("general-purpose")) is not None


@pytest.mark.parametrize("lookalike_type", ["dotfiles:explorer", "explore-and-edit"])
def test_an_agent_merely_named_like_explore_still_counts(
    interactive_session_with_isolated_state, lookalike_type
):
    subagent_budget_guard_handler.handle(spawn_of(lookalike_type))
    subagent_budget_guard_handler.handle(spawn_of(lookalike_type))
    assert subagent_budget_guard_handler.handle(spawn_of(lookalike_type)) is not None


def test_a_denial_tells_the_lead_that_scouts_stay_free(
    interactive_session_with_isolated_state,
):
    subagent_budget_guard_handler.handle(spawn_of("general-purpose"))
    subagent_budget_guard_handler.handle(spawn_of("general-purpose"))
    denial = subagent_budget_guard_handler.handle(spawn_of("general-purpose"))
    assert "explore scouts never count" in denial.system_message
