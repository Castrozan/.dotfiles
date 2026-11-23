from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ..round.markdown_table import clipped, markdown_table

FRESH_STATES = frozenset({"working", "waiting"})
HERDR_STATUSES = frozenset({"working", "idle", "done", "blocked"})
EXPECTED_PANE_STATUSES = {
    "working": frozenset({"working"}),
    "waiting": frozenset({"working", "idle", "done"}),
    None: frozenset({"working"}),
}
GONE_STATUS = "gone"
NO_HEARTBEAT_STATE = "no heartbeat"
OPEN_HEADERS = ["Session", "State", "Pane", "Heard", "Doing", "Next", "Flags"]
CLOSED_HEADERS = ["Session", "Closed", "Because"]
CLOSED_ROWS = 10
CELL_CHARACTERS = 70


@dataclass(frozen=True)
class SessionStatus:
    entry: dict
    heartbeat: dict | None
    pane_status: str


def published_heartbeat_of(entry: dict) -> dict | None:
    path = Path(entry["heartbeat"])
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def minutes_since(timestamp: str, now: datetime) -> int:
    return int((now - datetime.fromisoformat(timestamp)).total_seconds() // 60)


def quiet_flags(status: SessionStatus, now: datetime, bound: int) -> list[str]:
    heartbeat = status.heartbeat
    if heartbeat is None:
        quiet = minutes_since(status.entry["opened_at"], now)
        return [f"no heartbeat after {quiet}m"] if quiet > bound else []
    quiet = minutes_since(heartbeat["updated_at"], now)
    if heartbeat["state"] in FRESH_STATES and quiet > bound:
        return [f"stale {quiet}m"]
    return []


def pane_flags(status: SessionStatus) -> list[str]:
    if status.pane_status == GONE_STATUS:
        return ["pane gone"]
    state = status.heartbeat["state"] if status.heartbeat else None
    expected = EXPECTED_PANE_STATUSES.get(state, HERDR_STATUSES)
    if status.pane_status not in HERDR_STATUSES - expected:
        return []
    return [f"pane {status.pane_status} while {state or NO_HEARTBEAT_STATE}"]


def session_flags(status: SessionStatus, now: datetime, bound: int) -> list[str]:
    return quiet_flags(status, now, bound) + pane_flags(status)


def cell(text: str) -> str:
    return clipped(text, CELL_CHARACTERS)


def open_row(status: SessionStatus, now: datetime, bound: int) -> list[str]:
    heartbeat = status.heartbeat or {}
    heard = (
        f"{minutes_since(heartbeat['updated_at'], now)}m ago" if heartbeat else "never"
    )
    return [
        status.entry["name"],
        heartbeat.get("state", NO_HEARTBEAT_STATE),
        status.pane_status,
        heard,
        cell(heartbeat.get("doing", f"goal: {status.entry['goal']}")),
        cell(heartbeat.get("next", "-")),
        ", ".join(session_flags(status, now, bound)) or "none",
    ]


def closed_row(entry: dict) -> list[str]:
    return [entry["name"], entry["closed_at"], cell(entry["closed_because"])]


def open_block(statuses: list[SessionStatus], now: datetime, bound: int) -> str:
    if not statuses:
        return "No session is open."
    rows = [open_row(status, now, bound) for status in statuses]
    return markdown_table(OPEN_HEADERS, rows)


def closed_block(shown: list[dict], hidden: int) -> list[str]:
    if not shown:
        return ["No session has closed."]
    table = markdown_table(CLOSED_HEADERS, list(map(closed_row, shown)))
    return [table, *([f"Older closed sessions not shown: {hidden}."] if hidden else [])]


def rendered_status(
    statuses: list[SessionStatus], closed: list[dict], now: datetime, bound: int
) -> str:
    newest = sorted(closed, key=lambda entry: entry["closed_at"], reverse=True)
    shown = newest[:CLOSED_ROWS]
    listed = [status.entry for status in statuses] + shown
    pointers = [f"- {entry['name']}: {entry['heartbeat']}" for entry in listed]
    return "\n\n".join(
        [
            f"### Open sessions (stale after {bound}m)",
            open_block(statuses, now, bound),
            "### Closed sessions",
            *closed_block(shown, len(newest) - len(shown)),
            "### Heartbeat files",
            "\n".join(pointers) or "No session is indexed.",
        ]
    )
