from __future__ import annotations

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

import subagent_spawn_budget_state  # noqa: E402
from hook_dispatch import HandlerResult  # noqa: E402
from interactive_session_detection import (  # noqa: E402
    is_keyboard_driven_interactive_session,
)

SUBAGENT_SPAWN_TOOL_NAME = "Agent"
SUBAGENT_CEILING_BELOW_THE_ORCHESTRATED_TIER = 2
ORCHESTRATED_TIER_DECLARATION_TOKEN = "orchestrated"


def declares_the_orchestrated_tier(tool_input):
    return (
        (tool_input.get("description", "") or "")
        .strip()
        .lower()
        .startswith(ORCHESTRATED_TIER_DECLARATION_TOKEN)
    )


def build_ceiling_reached_message(allowed_spawn_count):
    return (
        f"BLOCKED: this session has already spawned {allowed_spawn_count} subagents, which is the "
        f"ceiling every tier below orchestrated holds to. Only five or more files, an auth, data or "
        f"public-interface change at any file count, more than two modules, requirements you cannot "
        f"restate, or a new public interface earn the orchestrated tier; a task sounding important "
        f"does not, and depth work loses the caller's context at the prompt boundary when it is fanned "
        f"out. Either work inside the ceiling and do the rest yourself, or re-attempt this spawn with "
        f"the Agent description starting with 'orchestrated:' followed by the trigger that justifies "
        f"it, which unlocks the remaining spawns for this session."
    )


def handle(hook_input):
    if hook_input.get("tool_name", "") != SUBAGENT_SPAWN_TOOL_NAME:
        return None
    if not is_keyboard_driven_interactive_session():
        return None
    session_id = hook_input.get("session_id", "")
    state = subagent_spawn_budget_state.read_subagent_spawn_budget_state(session_id)
    allowed_spawn_count = state[subagent_spawn_budget_state.ALLOWED_SPAWN_COUNT_KEY]
    spawn_declares_the_orchestrated_tier = declares_the_orchestrated_tier(
        hook_input.get("tool_input", {}) or {}
    )
    session_already_declared_the_orchestrated_tier = state[
        subagent_spawn_budget_state.ORCHESTRATED_TIER_DECLARED_KEY
    ]
    if (
        allowed_spawn_count >= SUBAGENT_CEILING_BELOW_THE_ORCHESTRATED_TIER
        and not session_already_declared_the_orchestrated_tier
        and not spawn_declares_the_orchestrated_tier
    ):
        ceiling_reached_message = build_ceiling_reached_message(allowed_spawn_count)
        return HandlerResult(
            decision="deny",
            reason=ceiling_reached_message,
            system_message=ceiling_reached_message,
        )
    subagent_spawn_budget_state.record_allowed_subagent_spawn(
        session_id, spawn_declares_the_orchestrated_tier
    )
    return None
