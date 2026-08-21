#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from servant_roster import SERVANT_ROSTER  # noqa: E402

DEFAULT_SERVANT_TEMPORARY_DIRECTORY = Path("/tmp")


def _servants_from_roster(roster_text: str) -> list[dict]:
    servants = []
    for roster_line in roster_text.strip().splitlines():
        if not roster_line.strip():
            continue
        name, _, personality = roster_line.partition("|")
        servants.append({"name": name.strip(), "personality": personality.strip()})
    return servants


SERVANT_CATALOG = _servants_from_roster(SERVANT_ROSTER)

assert len({entry["name"] for entry in SERVANT_CATALOG}) == len(SERVANT_CATALOG), (
    "every servant needs a unique name, because the name is the whole identity "
    "other agents address the session by"
)
assert all(entry["personality"] for entry in SERVANT_CATALOG), (
    "every servant needs a personality after the |, because it is the only part "
    "the session itself ever sees"
)


def select_servant_for_session(session_id: str) -> dict:
    seed_digest = hashlib.sha256((session_id or "unknown").encode("utf-8")).digest()
    seed = int.from_bytes(seed_digest[:8], "big")
    return SERVANT_CATALOG[seed % len(SERVANT_CATALOG)]


def servant_temporary_directory() -> Path:
    return Path(os.environ.get("TMPDIR") or DEFAULT_SERVANT_TEMPORARY_DIRECTORY)
