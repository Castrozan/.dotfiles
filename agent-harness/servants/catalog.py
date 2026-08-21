#!/usr/bin/env python3

from __future__ import annotations

import hashlib

from roster import SERVANT_ROSTER  # noqa: E402


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


def _pairing_score(session_id: str, servant_name: str) -> bytes:
    pair = f"{session_id or 'unknown'}\x00{servant_name}".encode("utf-8")
    return hashlib.sha256(pair).digest()


def select_servant_for_session(
    session_id: str, catalog: list[dict] | None = None
) -> dict:
    """The Servant this session is, scored per name rather than by list position.

    Indexing by `hash % len(catalog)` would tie every session to how many
    Servants exist, so adding one name re-drew every session on the fleet. Here
    each Servant scores itself against the session id and the highest wins, so
    the roster's length and order stop mattering: adding a name only moves the
    sessions that name now wins, and reordering the file moves nobody.
    """
    servants = SERVANT_CATALOG if catalog is None else catalog
    return max(
        servants, key=lambda servant: _pairing_score(session_id, servant["name"])
    )
