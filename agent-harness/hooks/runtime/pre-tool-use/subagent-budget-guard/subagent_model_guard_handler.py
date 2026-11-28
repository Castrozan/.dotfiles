from __future__ import annotations

import re
import sys
from pathlib import Path

_MODULE_DIRECTORY = Path(__file__).resolve().parent
for _shared_module_candidate_directory in [_MODULE_DIRECTORY] + [
    ancestor / "common" for ancestor in _MODULE_DIRECTORY.parents
]:
    _shared_module_candidate_path = str(_shared_module_candidate_directory)
    if (
        _shared_module_candidate_directory.is_dir()
        and _shared_module_candidate_path not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_path)

from hook_dispatch import HandlerResult  # noqa: E402
from interactive_session_detection import (  # noqa: E402
    is_keyboard_driven_interactive_session,
)

SUBAGENT_SPAWN_TOOL_NAME = "Agent"
CHEAP_MODEL_TIERS = frozenset({"haiku", "sonnet"})
CHEAP_PINNED_AGENT_TYPES = frozenset(
    {
        "dotfiles:explore",
        "dotfiles:quality-assurance",
        "dotfiles:runner",
        "dotfiles:software-engineer",
    }
)
MODEL_NAME_SEPARATOR = re.compile(r"[^a-z]+")


def names_a_cheap_model(model_name):
    name_words = set(MODEL_NAME_SEPARATOR.split(model_name.lower()))
    return not name_words.isdisjoint(CHEAP_MODEL_TIERS)


def is_a_cheap_pinned_agent_type(subagent_type):
    return subagent_type in CHEAP_PINNED_AGENT_TYPES


def build_top_tier_model_message(requested_model):
    return (
        f"BLOCKED: this spawn asks for model '{requested_model}', but every subagent runs on haiku or "
        f"sonnet. Delegated work is mechanical by definition, and a top-tier subagent re-reads its whole "
        f"context at top-tier price on every turn. Re-attempt with model 'haiku' for search, run and "
        f"report work or 'sonnet' for implementation. Work that needs the top tier belongs in this "
        f"session, not in a subagent."
    )


def build_unpinned_agent_type_message(subagent_type):
    shown_type = subagent_type or "general-purpose"
    return (
        f"BLOCKED: agent type '{shown_type}' carries no cheap model of its own, so it would inherit this "
        f"session's top-tier model. Re-attempt with the Agent model set to 'haiku' or 'sonnet', or use a "
        f"pinned type: dotfiles:explore for search, dotfiles:runner for run-and-wait sequences, "
        f"dotfiles:software-engineer for decided code changes, dotfiles:quality-assurance for review."
    )


def model_policy_denial_message(hook_input):
    if hook_input.get("tool_name", "") != SUBAGENT_SPAWN_TOOL_NAME:
        return None
    if not is_keyboard_driven_interactive_session():
        return None
    tool_input = hook_input.get("tool_input", {}) or {}
    requested_model = (tool_input.get("model", "") or "").strip()
    if requested_model:
        if names_a_cheap_model(requested_model):
            return None
        return build_top_tier_model_message(requested_model)
    subagent_type = (tool_input.get("subagent_type", "") or "").strip()
    if is_a_cheap_pinned_agent_type(subagent_type):
        return None
    return build_unpinned_agent_type_message(subagent_type)


def handle(hook_input):
    denial_message = model_policy_denial_message(hook_input)
    if denial_message is None:
        return None
    return HandlerResult(
        decision="deny", reason=denial_message, system_message=denial_message
    )
