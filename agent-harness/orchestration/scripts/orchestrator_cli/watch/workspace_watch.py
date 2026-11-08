from __future__ import annotations

import selectors
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..record_store import all_records
from .herdr_events import (
    decoded_messages,
    status_subscription,
    subscribed_socket,
    workspace_agent_panes,
    workspace_subscription,
)

REPORTED_STATUSES = frozenset({"blocked", "done", "idle"})


def status_line(data: dict) -> tuple[str | None, str | None]:
    if data.get("agent_status") not in REPORTED_STATUSES:
        return None, None
    title = data.get("title") or data.get("agent") or ""
    return f"{data['agent_status'].upper()} {data['pane_id']} {title}".rstrip(), None


def started_line(data: dict) -> tuple[str | None, str | None]:
    return f"STARTED {data['pane_id']}", data["pane_id"]


def exited_line(data: dict) -> tuple[str | None, str | None]:
    return f"EXITED {data['pane_id']}", None


EVENT_RENDERERS = {
    "pane.agent_status_changed": status_line,
    "pane.agent_detected": started_line,
    "pane.exited": exited_line,
    "pane.closed": exited_line,
}


def event_line(message: dict, workspace: str) -> tuple[str | None, str | None]:
    data = message.get("data") or {}
    render = EVENT_RENDERERS.get(message.get("event"))
    if render is None or data.get("workspace_id") != workspace:
        return None, None
    return render(data)


def stale_report_lines(
    report_directory: Path, pane_ids: set[str], safety_minutes: float
) -> list[str]:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=safety_minutes)
    return [
        f"STALE {report['name']} {report['state']} since {report['updated_at']}"
        for report in all_records(report_directory)
        if report.get("requester_pane") in pane_ids
        and report["state"] == "working"
        and datetime.fromisoformat(report["updated_at"]) < cutoff
    ]


class WorkspaceWatch:
    def __init__(self, workspace: str, report_directory: Path, safety_minutes: float):
        self.workspace = workspace
        self.report_directory = report_directory
        self.safety_minutes = safety_minutes
        self.selector = selectors.DefaultSelector()
        self.buffers: dict[int, bytes] = {}
        self.pane_ids: set[str] = set()
        self.last_safety_check = time.monotonic()

    def register(self, subscriptions: list[dict]) -> None:
        connection = subscribed_socket(subscriptions)
        self.buffers[connection.fileno()] = b""
        self.selector.register(connection, selectors.EVENT_READ)

    def watch_pane(self, pane_id: str) -> None:
        if pane_id not in self.pane_ids:
            self.pane_ids.add(pane_id)
            self.register(status_subscription(pane_id))

    def start(self) -> None:
        self.register(workspace_subscription())
        for pane in workspace_agent_panes(self.workspace):
            self.watch_pane(pane["pane_id"])

    def lines_from(self, connection) -> list[str]:
        chunk = connection.recv(65536)
        if not chunk:
            self.selector.unregister(connection)
            connection.close()
            return []
        messages, self.buffers[connection.fileno()] = decoded_messages(
            self.buffers[connection.fileno()] + chunk
        )
        lines = []
        for message in messages:
            line, new_pane = event_line(message, self.workspace)
            if new_pane:
                self.watch_pane(new_pane)
            if line:
                lines.append(line)
        return lines

    def safety_lines(self) -> list[str]:
        self.last_safety_check = time.monotonic()
        return stale_report_lines(
            self.report_directory, self.pane_ids, self.safety_minutes
        )

    def next_lines(self) -> list[str]:
        safety_seconds = self.safety_minutes * 60
        remaining = safety_seconds - (time.monotonic() - self.last_safety_check)
        if remaining <= 0:
            return self.safety_lines()
        ready = self.selector.select(timeout=remaining)
        return [line for key, _ in ready for line in self.lines_from(key.fileobj)]
