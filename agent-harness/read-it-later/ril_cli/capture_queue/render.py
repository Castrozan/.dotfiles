from __future__ import annotations

import json

STATE_COLUMN_WIDTH = 11


def render_capture_row(position: int, capture: dict[str, str | None]) -> str:
    state_column = str(capture["state"]).ljust(STATE_COLUMN_WIDTH)
    held_by_suffix = (
        f"  (held by {capture['claimed_by']})" if capture["state"] == "working" else ""
    )
    return (
        f"{position:>4}  {state_column}  {capture['captured']}  "
        f"{capture['name']}{held_by_suffix}"
    )


def render_pending_captures_as_text(
    pending_captures: list[dict[str, str | None]], total_count: int
) -> str:
    rendered_rows = [
        render_capture_row(position, capture)
        for position, capture in enumerate(pending_captures, 1)
    ]
    header = f"{total_count} pending captures, newest first"
    if len(pending_captures) < total_count:
        header = f"{header}, showing {len(pending_captures)}"
    return "\n".join([header, *rendered_rows])


def render_pending_captures_as_json(
    pending_captures: list[dict[str, str | None]], total_count: int
) -> str:
    return json.dumps({"total": total_count, "captures": pending_captures}, indent=2)
