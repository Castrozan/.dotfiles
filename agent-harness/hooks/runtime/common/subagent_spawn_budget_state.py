from __future__ import annotations

import json
import os
import re
import fcntl
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


def normalized_subagent_spawn_budget_state(stored_state):
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


def read_subagent_spawn_budget_state(session_id):
    try:
        stored_state = json.loads(
            subagent_spawn_budget_state_path(session_id).read_text()
        )
    except (OSError, ValueError):
        return empty_subagent_spawn_budget_state()
    return normalized_subagent_spawn_budget_state(stored_state)


def reserve_subagent_spawn(
    session_id, declares_the_orchestrated_tier, allowed_spawn_ceiling
):
    state_path = subagent_spawn_budget_state_path(session_id)
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with state_path.open("a+") as state_file:
            fcntl.flock(state_file.fileno(), fcntl.LOCK_EX)
            state_file.seek(0)
            try:
                state = normalized_subagent_spawn_budget_state(
                    json.loads(state_file.read())
                )
            except ValueError:
                state = empty_subagent_spawn_budget_state()
            if (
                state[ALLOWED_SPAWN_COUNT_KEY] >= allowed_spawn_ceiling
                and not state[ORCHESTRATED_TIER_DECLARED_KEY]
                and not declares_the_orchestrated_tier
            ):
                return False
            state[ALLOWED_SPAWN_COUNT_KEY] += 1
            state[ORCHESTRATED_TIER_DECLARED_KEY] = (
                state[ORCHESTRATED_TIER_DECLARED_KEY] or declares_the_orchestrated_tier
            )
            state_file.seek(0)
            state_file.truncate()
            json.dump(state, state_file)
            state_file.flush()
            os.fsync(state_file.fileno())
            return True
    except OSError:
        return False
