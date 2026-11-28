import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from hook_module_loader import import_hyphenated_hook_module

subagent_model_guard_handler = import_hyphenated_hook_module(
    "subagent_model_guard_handler"
)
subagent_budget_guard_handler = import_hyphenated_hook_module(
    "subagent_budget_guard_handler"
)
subagent_spawn_budget_state = import_hyphenated_hook_module(
    "subagent_spawn_budget_state"
)

SUBAGENT_DEFINITIONS_DIRECTORY = (
    Path(__file__).resolve().parents[6]
    / "agent-instructions"
    / "rulesync"
    / "sources"
    / "subagents"
)
CLAUDE_CODE_MODEL_PIN = re.compile(r"^claudecode:\n(?:  .*\n)*?  model: (\w+)", re.M)
PINNED_TYPES = sorted(subagent_model_guard_handler.CHEAP_PINNED_AGENT_TYPES)


@pytest.fixture
def interactive_session(monkeypatch, tmp_path):
    monkeypatch.setenv(
        "AGENT_INTERACTIVE_PREFERENCES_PATH", "/nix/store/interactive-communication.md"
    )
    monkeypatch.delenv("CLAWDE_AGENT_NAME", raising=False)
    monkeypatch.setenv(
        subagent_spawn_budget_state.STATE_DIRECTORY_OVERRIDE_ENVIRONMENT_VARIABLE,
        str(tmp_path),
    )


def spawn_of(subagent_type="", model=None):
    tool_input = {"description": "do it", "prompt": "do the work"}
    if subagent_type:
        tool_input["subagent_type"] = subagent_type
    if model:
        tool_input["model"] = model
    return {
        "tool_name": "Agent",
        "session_id": "session-under-test",
        "tool_input": tool_input,
    }


@pytest.mark.parametrize(
    "model",
    ["opus", "fable", "claude-opus-5-5", "claude-fable-5-2", "opus[1m]", "inherit"],
)
@pytest.mark.parametrize("subagent_type", ["", "general-purpose", *PINNED_TYPES])
def test_a_top_tier_or_inherited_model_is_denied_for_every_agent_type(
    interactive_session, subagent_type, model
):
    denial = subagent_model_guard_handler.handle(spawn_of(subagent_type, model))

    assert denial.decision == "deny"


@pytest.mark.parametrize(
    "model",
    ["haiku", "sonnet", "Haiku", "claude-haiku-5-5", "claude-sonnet-5-5", "sonnet[1m]"],
)
@pytest.mark.parametrize(
    "subagent_type", ["", "general-purpose", "Explore", *PINNED_TYPES]
)
def test_a_cheap_model_is_allowed_for_every_agent_type(
    interactive_session, subagent_type, model
):
    assert subagent_model_guard_handler.handle(spawn_of(subagent_type, model)) is None


@pytest.mark.parametrize("subagent_type", PINNED_TYPES)
def test_a_pinned_agent_type_may_omit_the_model(interactive_session, subagent_type):
    assert subagent_model_guard_handler.handle(spawn_of(subagent_type)) is None


@pytest.mark.parametrize(
    "subagent_type",
    [
        "",
        "general-purpose",
        "Explore",
        "Plan",
        "web-fetch",
        "explore",
        "dotfiles:explorer",
    ],
)
def test_an_unpinned_agent_type_must_name_a_cheap_model(
    interactive_session, subagent_type
):
    denial = subagent_model_guard_handler.handle(spawn_of(subagent_type))

    assert denial.decision == "deny"


def test_a_denial_names_both_cheap_tiers_and_the_pinned_types(interactive_session):
    denial = subagent_model_guard_handler.handle(spawn_of("general-purpose"))

    assert "haiku" in denial.system_message and "sonnet" in denial.system_message
    assert "dotfiles:runner" in denial.system_message


def test_the_guard_stays_out_of_background_agent_sessions(monkeypatch):
    monkeypatch.delenv("AGENT_INTERACTIVE_PREFERENCES_PATH", raising=False)

    assert subagent_model_guard_handler.handle(spawn_of("", "opus")) is None


def test_the_guard_ignores_other_tools(interactive_session):
    hook_input = {"tool_name": "Bash", "tool_input": {"model": "opus"}}

    assert subagent_model_guard_handler.handle(hook_input) is None


def test_a_denied_spawn_consumes_no_spawn_budget(interactive_session):
    for _ in range(5):
        assert subagent_budget_guard_handler.handle(spawn_of("general-purpose")) is None
    assert subagent_budget_guard_handler.handle(spawn_of("", "sonnet")) is None
    assert subagent_budget_guard_handler.handle(spawn_of("", "sonnet")) is None
    assert subagent_budget_guard_handler.handle(spawn_of("", "sonnet")) is not None


def test_every_subagent_definition_pins_a_cheap_claude_code_model():
    definitions = sorted(SUBAGENT_DEFINITIONS_DIRECTORY.glob("*.md"))

    assert definitions
    for definition in definitions:
        pin = CLAUDE_CODE_MODEL_PIN.search(definition.read_text())
        assert pin is not None, f"{definition.stem} carries no claudecode model pin"
        assert subagent_model_guard_handler.names_a_cheap_model(pin.group(1))


def test_the_guard_pins_exactly_the_agent_types_the_definitions_provide():
    defined_types = {
        f"dotfiles:{definition.stem}"
        for definition in SUBAGENT_DEFINITIONS_DIRECTORY.glob("*.md")
    }

    assert defined_types == set(subagent_model_guard_handler.CHEAP_PINNED_AGENT_TYPES)
