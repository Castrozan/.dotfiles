#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from servant_roster_caster import (  # noqa: E402
    CASTER_CLASS_SERVANT_CATALOG,
)
from servant_roster_warrior import (  # noqa: E402
    WARRIOR_CLASS_SERVANT_CATALOG,
)

DEFAULT_SERVANT_TEMPORARY_DIRECTORY = Path("/tmp")

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
    return Path(os.environ.get("TMPDIR") or DEFAULT_SERVANT_TEMPORARY_DIRECTORY)
