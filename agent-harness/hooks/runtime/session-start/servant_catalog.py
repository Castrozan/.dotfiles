#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from servant_roster_caster import (  # noqa: E402
    CASTER_CLASS_SERVANT_CATALOG,
)
from servant_roster_warrior import (  # noqa: E402
    WARRIOR_CLASS_SERVANT_CATALOG,
)

SERVANT_IDENTITY_STATE_DIRECTORY_ENVIRONMENT_VARIABLE = (
    "SERVANT_IDENTITY_STATE_DIRECTORY"
)
DEFAULT_SERVANT_IDENTITY_STATE_DIRECTORY = Path("/tmp")

SERVANT_CATALOG = WARRIOR_CLASS_SERVANT_CATALOG + CASTER_CLASS_SERVANT_CATALOG

_UNIQUE_SERVANT_KEYS = {(entry["name"], entry["class"]) for entry in SERVANT_CATALOG}
assert len(_UNIQUE_SERVANT_KEYS) == len(SERVANT_CATALOG), (
    "every servant entry needs a unique (name, class) key, because Artoria Saber "
    "and Artoria Lancer are different servants"
)


def select_servant_for_session(session_id: str) -> dict:
    seed_digest = hashlib.sha256((session_id or "unknown").encode("utf-8")).digest()
    seed = int.from_bytes(seed_digest[:8], "big")
    return SERVANT_CATALOG[seed % len(SERVANT_CATALOG)]


def servant_temporary_directory() -> Path:
    return Path(os.environ.get("TMPDIR") or DEFAULT_SERVANT_IDENTITY_STATE_DIRECTORY)


def servant_summoned_at_launch() -> dict | None:
    """The Servant the launch wrapper already chose, read back from the environment.

    The wrapper summons before the session exists, so the hook adopts that choice
    instead of drawing a second, contradictory one for the same session.
    """
    name = os.environ.get("SERVANT_NAME", "").strip()
    if not name:
        return None
    return {
        "name": name,
        "class": os.environ.get("SERVANT_CLASS", "").strip(),
        "manner": os.environ.get("SERVANT_MANNER", "").strip(),
    }


def servant_identity_state_path(session_id: str) -> Path:
    sanitized_session_id = re.sub(r"[^a-zA-Z0-9_-]+", "-", session_id or "unknown")
    state_directory = os.environ.get(
        SERVANT_IDENTITY_STATE_DIRECTORY_ENVIRONMENT_VARIABLE
    )
    if state_directory:
        base_directory = Path(state_directory)
    else:
        base_directory = DEFAULT_SERVANT_IDENTITY_STATE_DIRECTORY
    return base_directory / f"servant-identity-{sanitized_session_id}.json"


def read_servant_identity(session_id: str) -> dict | None:
    try:
        stored_identity = json.loads(
            servant_identity_state_path(session_id).read_text()
        )
    except (OSError, ValueError):
        return None
    if not isinstance(stored_identity, dict):
        return None
    return stored_identity


def write_servant_identity(session_id: str, servant: dict) -> None:
    state_path = servant_identity_state_path(session_id)
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(servant), encoding="utf-8")
    except OSError:
        pass
