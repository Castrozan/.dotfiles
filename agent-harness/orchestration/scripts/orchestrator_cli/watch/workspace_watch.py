from __future__ import annotations

import selectors
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from ..record_store import all_records
from .herdr_events import (
    decoded_messages,
    status_subscription,
    subscribed_socket,
    workspace_agent_panes,
    workspace_subscription,
)
from .session_timeouts import (
    SessionRecords,
    WatchedSession,
    current_time,
    is_finished,
    session_deadline,
    session_records,
    timeout_line,
)

REPORTED_STATUSES = frozenset({"blocked", "done", "idle"})
STATUS_CHANGED_EVENT = "pane.agent_status_changed"
PANE_GONE_EVENTS = frozenset({"pane.exited", "pane.closed"})


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
    STATUS_CHANGED_EVENT: status_line,
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


@dataclass(frozen=True)
class WatchConfiguration:
    workspace: str
    report_directory: Path
    decision_directory: Path
    timeout_minutes: float
    followed_panes: frozenset[str]
    own_pane: str | None


class WorkspaceWatch:
    def __init__(self, configuration: WatchConfiguration):
        self.configuration = configuration
        self.timeout = timedelta(minutes=configuration.timeout_minutes)
        self.selector = selectors.DefaultSelector()
        self.buffers: dict[int, bytes] = {}
        self.sessions: dict[str, WatchedSession] = {}
        self.next_check_at = current_time()

    def follows(self, pane_id: str | None) -> bool:
        followed = self.configuration.followed_panes
        return pane_id != self.configuration.own_pane and (
            not followed or pane_id in followed
        )

    def register(self, subscriptions: list[dict]) -> None:
        connection = subscribed_socket(subscriptions)
        self.buffers[connection.fileno()] = b""
        self.selector.register(connection, selectors.EVENT_READ)

    def watch_pane(self, pane_id: str, status: str = "unknown") -> None:
        if pane_id in self.sessions or not self.follows(pane_id):
            return
        self.sessions[pane_id] = WatchedSession(pane_id, status, current_time())
        self.register(status_subscription(pane_id))

    def start(self) -> None:
        self.register(workspace_subscription())
        for pane in workspace_agent_panes(self.configuration.workspace):
            self.watch_pane(pane["pane_id"], pane.get("agent_status", "unknown"))

    def observe(self, event: str | None, data: dict) -> None:
        session = self.sessions.get(data.get("pane_id"))
        if session is None:
            return
        if event == STATUS_CHANGED_EVENT:
            session.status = data.get("agent_status", session.status)
            session.heard_at = current_time()
        elif event in PANE_GONE_EVENTS:
            del self.sessions[session.pane_id]

    def line_from_message(self, message: dict) -> str | None:
        data = message.get("data") or {}
        if not self.follows(data.get("pane_id")):
            return None
        line, new_pane = event_line(message, self.configuration.workspace)
        if new_pane:
            self.watch_pane(new_pane)
        self.observe(message.get("event"), data)
        return line

    def lines_from(self, connection) -> list[str]:
        chunk = connection.recv(65536)
        if not chunk:
            self.selector.unregister(connection)
            connection.close()
            return []
        messages, self.buffers[connection.fileno()] = decoded_messages(
            self.buffers[connection.fileno()] + chunk
        )
        return list(filter(None, map(self.line_from_message, messages)))

    def current_records(self) -> SessionRecords:
        return session_records(
            all_records(self.configuration.report_directory),
            all_records(self.configuration.decision_directory),
        )

    def check_timeouts(self) -> list[str]:
        now = current_time()
        records = self.current_records()
        pending = [
            session
            for session in self.sessions.values()
            if not is_finished(session, records)
        ]
        overdue = [
            session
            for session in pending
            if session_deadline(session, records, self.timeout) <= now
        ]
        for session in overdue:
            session.reminded_at = now
        self.next_check_at = min(
            (session_deadline(session, records, self.timeout) for session in pending),
            default=now + self.timeout,
        )
        return [timeout_line(session, records, now) for session in overdue]

    def next_lines(self) -> list[str]:
        remaining = (self.next_check_at - current_time()).total_seconds()
        if remaining <= 0:
            return self.check_timeouts()
        wait_seconds = min(remaining, self.timeout.total_seconds())
        ready = self.selector.select(timeout=wait_seconds)
        return [line for key, _ in ready for line in self.lines_from(key.fileobj)]
