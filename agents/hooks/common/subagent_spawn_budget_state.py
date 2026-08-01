from __future__ import annotations

import json
import os
import re
from pathlib import Path

STATE_DIRECTORY_OVERRIDE_ENVIRONMENT_VARIABLE = "SUBAGENT_SPAWN_BUDGET_STATE_DIRECTORY"
ALLOWED_SPAWN_COUNT_KEY = "allowed_subagent_spawn_count"
ORCHESTRATED_TIER_DECLARED_KEY = "orchestrated_tier_declared"


def resolve_state_directory():
    override = os.environ.get(STATE_DIRECTORY_OVERRIDE_ENVIRONMENT_VARIABLE)
    if override:
        return Path(override)
    return Path("/tmp")


def subagent_spawn_budget_state_path(session_id):
    sanitized_session_id = re.sub(r"[^a-zA-Z0-9_-]+", "-", session_id or "unknown")
    return (
        resolve_state_directory() / f"subagent-spawn-budget-{sanitized_session_id}.json"
    )


def coerced_allowed_spawn_count(value):
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def empty_subagent_spawn_budget_state():
    return {ALLOWED_SPAWN_COUNT_KEY: 0, ORCHESTRATED_TIER_DECLARED_KEY: False}


def read_subagent_spawn_budget_state(session_id):
    try:
        stored_state = json.loads(
            subagent_spawn_budget_state_path(session_id).read_text()
        )
    except (OSError, ValueError):
        return empty_subagent_spawn_budget_state()
    if not isinstance(stored_state, dict):
        return empty_subagent_spawn_budget_state()
    return {
        ALLOWED_SPAWN_COUNT_KEY: coerced_allowed_spawn_count(
            stored_state.get(ALLOWED_SPAWN_COUNT_KEY)
        ),
        ORCHESTRATED_TIER_DECLARED_KEY: bool(
            stored_state.get(ORCHESTRATED_TIER_DECLARED_KEY)
        ),
    }


def write_subagent_spawn_budget_state(session_id, state):
    state_path = subagent_spawn_budget_state_path(session_id)
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state))
    except OSError:
        return


def record_allowed_subagent_spawn(session_id, declares_the_orchestrated_tier):
    state = read_subagent_spawn_budget_state(session_id)
    state[ALLOWED_SPAWN_COUNT_KEY] += 1
    state[ORCHESTRATED_TIER_DECLARED_KEY] = (
        state[ORCHESTRATED_TIER_DECLARED_KEY] or declares_the_orchestrated_tier
    )
    write_subagent_spawn_budget_state(session_id, state)
    return state
