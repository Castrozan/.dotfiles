import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from hook_module_loader import import_hyphenated_hook_module

subagent_model_guard_handler = import_hyphenated_hook_module(
    "subagent_model_guard_handler"
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
TOP_TIER_MODELS = ["opus", "fable", "claude-opus-5-5", "opus[1m]", "inherit"]
CHEAP_MODELS = ["haiku", "Haiku", "claude-sonnet-5-5", "sonnet[1m]"]
UNPINNED_TYPES = [
    "",
    "general-purpose",
    "Explore",
    "Plan",
    "explore",
    "dotfiles:explorer",
]
SPAWN_POLICY_CASES = (
    [
        ("Agent", True, kind, model, True)
        for model in TOP_TIER_MODELS
        for kind in ["", *PINNED_TYPES]
    ]
    + [
        ("Agent", True, kind, model, False)
        for model in CHEAP_MODELS
        for kind in [*UNPINNED_TYPES, *PINNED_TYPES]
    ]
    + [("Agent", True, kind, None, False) for kind in PINNED_TYPES]
    + [("Agent", True, kind, None, True) for kind in UNPINNED_TYPES]
    + [("Agent", True, "fork", model, True) for model in [None, "haiku", "sonnet"]]
    + [("Bash", True, "", "opus", False), ("Agent", False, "", "opus", False)]
)


@pytest.mark.parametrize(
    "tool_name, interactive, subagent_type, model, denied", SPAWN_POLICY_CASES
)
def test_spawn_policy_denies_exactly_what_would_run_above_the_cheap_tiers(
    monkeypatch, tool_name, interactive, subagent_type, model, denied
):
    monkeypatch.delenv("CLAWDE_AGENT_NAME", raising=False)
    if interactive:
        monkeypatch.setenv("AGENT_INTERACTIVE_PREFERENCES_PATH", "/nix/store/x.md")
    else:
        monkeypatch.delenv("AGENT_INTERACTIVE_PREFERENCES_PATH", raising=False)
    tool_input = {"description": "do it", "prompt": "do the work"}
    tool_input.update({"subagent_type": subagent_type} if subagent_type else {})
    tool_input.update({"model": model} if model else {})

    result = subagent_model_guard_handler.handle(
        {"tool_name": tool_name, "tool_input": tool_input}
    )

    assert (result is not None) == denied
    if denied:
        assert result.decision == "deny"
        assert "haiku" in result.system_message and "sonnet" in result.system_message


def test_the_definitions_pin_cheap_models_and_the_guard_lists_exactly_them():
    definitions = sorted(SUBAGENT_DEFINITIONS_DIRECTORY.glob("*.md"))

    assert definitions
    for definition in definitions:
        pin = CLAUDE_CODE_MODEL_PIN.search(definition.read_text())
        assert pin is not None, f"{definition.stem} carries no claudecode model pin"
        assert subagent_model_guard_handler.names_a_cheap_model(pin.group(1))
    assert {f"dotfiles:{definition.stem}" for definition in definitions} == set(
        PINNED_TYPES
    )
