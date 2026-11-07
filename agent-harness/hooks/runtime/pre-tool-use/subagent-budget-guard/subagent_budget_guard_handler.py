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
READ_ONLY_SCOUT_AGENT_NAME = "explore"


def spawns_a_read_only_scout(tool_input):
    subagent_type = (tool_input.get("subagent_type", "") or "").strip().lower()
    return subagent_type.rsplit(":", 1)[-1] == READ_ONLY_SCOUT_AGENT_NAME


def spawn_counts_against_the_ceiling(hook_input):
    return (
        hook_input.get("tool_name", "") == SUBAGENT_SPAWN_TOOL_NAME
        and is_keyboard_driven_interactive_session()
        and not spawns_a_read_only_scout(hook_input.get("tool_input", {}) or {})
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
        f"it, which unlocks the remaining spawns for this session. Read-only explore scouts never "
        f"count against the ceiling."
    )


def handle(hook_input):
    if not spawn_counts_against_the_ceiling(hook_input):
        return None
    session_id = hook_input.get("session_id", "")
    spawn_declares_the_orchestrated_tier = (
        subagent_spawn_budget_state.declares_the_orchestrated_tier(
            hook_input.get("tool_input", {}) or {}
        )
    )
    if not subagent_spawn_budget_state.reserve_subagent_spawn(
        session_id,
        spawn_declares_the_orchestrated_tier,
        subagent_spawn_budget_state.SUBAGENT_CEILING_BELOW_THE_ORCHESTRATED_TIER,
    ):
        ceiling_reached_message = build_ceiling_reached_message(
            subagent_spawn_budget_state.SUBAGENT_CEILING_BELOW_THE_ORCHESTRATED_TIER
        )
        return HandlerResult(
            decision="deny",
            reason=ceiling_reached_message,
            system_message=ceiling_reached_message,
        )
    return None
