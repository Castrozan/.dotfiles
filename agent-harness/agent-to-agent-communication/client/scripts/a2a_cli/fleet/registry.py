"""SQLite metadata only. This database never reads harness session stores."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
import time
from pathlib import Path

ACTIVE = (
    "dispatching",
    "dispatched",
    "working",
    "blocked",
    "uncertain",
    "reported_completed",
)
STATES = {"idle", "working", "blocked", "done", "unknown"}


def label(value, field):
    if not isinstance(value, str) or not value.strip() or len(value) > 512:
        raise ValueError(f"{field} must be a nonempty string of at most 512 characters")
    if any(ord(c) < 32 for c in value):
        raise ValueError(f"{field} must not contain control characters")
    return value


def normalize(directory, reply):
    """Join the real A2A directory and Herdr snapshot by structural pane ID."""
    if not isinstance(directory, dict) or not isinstance(reply, dict):
        raise ValueError("expected A2A directory and Herdr snapshot objects")
    result = reply.get("result")
    snapshot = result.get("snapshot") if isinstance(result, dict) else None
    if (
        not isinstance(snapshot, dict)
        or not isinstance(snapshot.get("version"), str)
        or not isinstance(snapshot.get("protocol"), int)
    ):
        raise ValueError("missing Herdr snapshot version/protocol")
    if any(
        not isinstance(snapshot.get(key), list)
        for key in ("agents", "panes", "tabs", "workspaces", "layouts")
    ):
        raise ValueError("incomplete Herdr snapshot collections")
    peers = {}
    for peer in directory.values():
        if not isinstance(peer, dict):
            raise ValueError("invalid A2A peer")
        pane = label(peer.get("paneId"), "paneId")
        if pane in peers:
            raise ValueError("duplicate A2A pane identity")
        peers[pane] = label(peer.get("name"), "peer name")
    rows, seen = [], set()
    for agent in snapshot["agents"]:
        if not isinstance(agent, dict):
            raise ValueError("invalid Herdr agent")
        pane = label(agent.get("pane_id"), "pane_id")
        if pane in seen:
            raise ValueError("duplicate Herdr pane identity")
        seen.add(pane)
        identity = agent.get("agent_session") or {}
        if not isinstance(identity, dict):
            raise ValueError("invalid Herdr session reference")
        # Path references are deliberately neither retained nor opened.
        session = (
            label(identity.get("value"), "session ID")
            if identity.get("kind") == "id"
            else ""
        )
        state = agent.get("agent_status", "unknown")
        if state not in STATES:
            raise ValueError("unknown Herdr agent status")
        rows.append(
            {
                "pane_id": pane,
                "session_id": session or None,
                "agent_id": pane,
                "name": peers.get(pane) or agent.get("name"),
                "harness": agent.get("agent"),
                "tab_id": agent.get("tab_id"),
                "workspace_id": agent.get("workspace_id"),
                "state": state,
                "interactive_ready": agent.get("interactive_ready") is True,
                "launch_pending": agent.get("launch_pending") is not False,
                "delivery_readiness": "unverified",
                "capabilities": ["a2a.dispatch", "a2a.status"] if pane in peers else [],
                "blockers": (["session_identity_unavailable"] if not session else [])
                + (["agent_requires_input"] if state == "blocked" else []),
            }
        )
    # An A2A pane missing from Herdr is an inconsistent snapshot, not proof of idle.
    if set(peers) - seen:
        raise ValueError("A2A and Herdr inventories disagree; refresh again")
    return rows


class Registry:
    def __init__(self, path, clock=time.time):
        self.clock = clock
        path = Path(path).expanduser()
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            stat = os.fstat(fd)
            if stat.st_uid != os.getuid() or stat.st_mode & 0o077:
                raise ValueError("registry must be owned by this user and mode 0600")
        finally:
            os.close(fd)
        self.db = sqlite3.connect(path, timeout=2)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA synchronous=FULL")
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, 1):
            self.db.close()
            raise ValueError("unsupported fleet registry schema")
        with self.db:
            self.db.executescript("""
                CREATE TABLE IF NOT EXISTS hosts (id TEXT PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS agents (
                    host TEXT, pane TEXT, session TEXT, data TEXT NOT NULL,
                    PRIMARY KEY(host, pane, session));
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY, host TEXT, pane TEXT, session TEXT,
                    state TEXT, data TEXT NOT NULL);
                CREATE UNIQUE INDEX IF NOT EXISTS one_active_job ON jobs(host, pane)
                    WHERE state IN ('dispatching','dispatched','working','blocked',
                                    'uncertain','reported_completed');
                PRAGMA user_version=1;
            """)

    def close(self):
        self.db.close()

    def host(self, host):
        row = self.db.execute("SELECT data FROM hosts WHERE id=?", (host,)).fetchone()
        if row is None:
            raise ValueError("unconfirmed host; register reviewed host evidence first")
        return json.loads(row[0])

    def confirm_host(self, host, transport, evidence):
        label(host, "host ID")
        label(evidence, "confirmation evidence reference")
        if transport != "local" and not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", transport
        ):
            raise ValueError("transport must be local or an existing SSH alias")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            previous = self.db.execute(
                "SELECT data FROM hosts WHERE id=?", (host,)
            ).fetchone()
            if previous:
                if json.loads(previous[0])["transport"] != transport:
                    raise ValueError("host identity cannot be silently remapped")
                return
            data = {
                "host_id": host,
                "transport": transport,
                "confirmation": evidence,
                "confirmed_at": self.clock(),
                "last_seen": None,
                "last_attempt": None,
                "observation": "unknown",
                "blocker": None,
                "refresh_required": False,
            }
            self.db.execute("INSERT INTO hosts VALUES (?,?)", (host, json.dumps(data)))

    def ingest(self, host, directory, snapshot, observed_at, evidence, source="cached"):
        if source not in {"live", "cached"}:
            raise ValueError("invalid evidence source")
        label(evidence, "evidence reference")
        if (
            not isinstance(observed_at, (int, float))
            or not math.isfinite(observed_at)
            or observed_at < 0
            or observed_at > self.clock() + 5
        ):
            raise ValueError("invalid or future evidence timestamp")
        rows = normalize(directory, snapshot)
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            h = self.host(host)
            if h["last_seen"] is not None and observed_at <= h["last_seen"]:
                return False
            old = self.db.execute(
                "SELECT pane,session,data FROM agents WHERE host=? AND json_extract(data, '$.present')=1",
                (host,),
            ).fetchall()
            for previous in old:
                data = json.loads(previous["data"])
                data["present"] = False
                self.db.execute(
                    "UPDATE agents SET data=? WHERE host=? AND pane=? AND session=?",
                    (json.dumps(data), host, previous["pane"], previous["session"]),
                )
            for row in rows:
                session = row["session_id"] or ""
                previous = self.db.execute(
                    "SELECT data FROM agents WHERE host=? AND pane=? AND session=?",
                    (host, row["pane_id"], session),
                ).fetchone()
                owned = json.loads(previous[0]) if previous else {}
                row.update(
                    host_id=host,
                    present=True,
                    last_seen=observed_at,
                    source=source,
                    evidence=evidence,
                    owner=owned.get("owner"),
                    task=owned.get("task"),
                )
                self.db.execute(
                    "INSERT OR REPLACE INTO agents VALUES (?,?,?,?)",
                    (host, row["pane_id"], session, json.dumps(row)),
                )
            h.update(
                last_seen=observed_at,
                last_attempt=self.clock(),
                observation="reachable",
                blocker=None,
                refresh_required=False,
            )
            self.db.execute("UPDATE hosts SET data=? WHERE id=?", (json.dumps(h), host))
        return True

    def failure(self, host, kind):
        if kind not in {"unreachable", "failed"}:
            raise ValueError("invalid observation failure")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            h = self.host(host)
            h.update(last_attempt=self.clock(), observation=kind, blocker=kind)
            self.db.execute("UPDATE hosts SET data=? WHERE id=?", (json.dumps(h), host))

    def agent(self, host, pane, session):
        row = self.db.execute(
            "SELECT data FROM agents WHERE host=? AND pane=? AND session=?",
            (host, pane, session),
        ).fetchone()
        if row is None:
            raise ValueError("agent/session identity has not been observed")
        return json.loads(row[0])

    def assign(self, host, pane, session, owner, task):
        label(owner, "owner")
        label(task, "task reference")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            row = self.agent(host, pane, session)
            row.update(owner=owner, task=task)
            self.db.execute(
                "UPDATE agents SET data=? WHERE host=? AND pane=? AND session=?",
                (json.dumps(row), host, pane, session),
            )

    def status(self, live_hosts=(), freshness=300, limit=500):
        if not 1 <= limit <= 1000:
            raise ValueError("status limit must be between 1 and 1000")
        now = self.clock()
        hosts = [
            json.loads(r[0])
            for r in self.db.execute(
                "SELECT data FROM hosts ORDER BY id LIMIT ?", (limit,)
            )
        ]
        agents = [
            json.loads(r[0])
            for r in self.db.execute(
                "SELECT data FROM agents ORDER BY json_extract(data, '$.present') DESC, host,pane,session LIMIT ?",
                (limit,),
            )
        ]
        jobs = [
            json.loads(r[0])
            for r in self.db.execute(
                "SELECT data FROM jobs ORDER BY json_extract(data, '$.updated_at') DESC,id LIMIT ?",
                (limit,),
            )
        ]
        invalidated = {row["host_id"] for row in hosts if row.get("refresh_required")}
        for row in hosts + agents:
            last = row["last_seen"]
            row["age_seconds"] = None if last is None else max(0, now - last)
            row["refresh_required"] = row["host_id"] in invalidated
            row["fresh"] = (
                last is not None
                and 0 <= now - last <= freshness
                and not row["refresh_required"]
            )
            row["view"] = (
                "live"
                if row["host_id"] in live_hosts and row.get("present", True)
                else "cached"
            )
        return {
            "schema_version": 1,
            "limit": limit,
            "counts": {
                table: self.db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                for table in ("hosts", "agents", "jobs")
            },
            "as_of": now,
            "hosts": hosts,
            "agents": agents,
            "jobs": jobs,
        }

    def job(self, request_id):
        row = self.db.execute(
            "SELECT data FROM jobs WHERE id=?", (request_id,)
        ).fetchone()
        return json.loads(row[0]) if row else None

    def reserve(self, request_id, host, pane, session, owner, task, prompt):
        for field, value in [
            ("request ID", request_id),
            ("session", session),
            ("owner", owner),
            ("task", task),
        ]:
            label(value, field)
        if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", request_id):
            raise ValueError("request ID must be a simple correlation token")
        fingerprint = hashlib.sha256(
            json.dumps([host, pane, session, owner, task, prompt]).encode()
        ).hexdigest()
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            previous = self.job(request_id)
            if previous:
                if previous["fingerprint"] != fingerprint:
                    raise ValueError(
                        "request ID already belongs to a different dispatch"
                    )
                return previous, False
            agent = self.agent(host, pane, session)
            h = self.host(host)
            age = self.clock() - agent["last_seen"]
            if (
                not agent["present"]
                or agent["state"] != "idle"
                or not agent["interactive_ready"]
                or agent["launch_pending"]
                or agent["source"] != "live"
                or not 0 <= age <= 30
                or h["observation"] != "reachable"
                or h.get("refresh_required")
            ):
                raise ValueError(
                    "dispatch requires a freshly resolved idle live session with readiness metadata"
                )
            if "a2a.dispatch" not in agent["capabilities"]:
                raise ValueError("session is not currently in A2A")
            data = {
                "request_id": request_id,
                "host_id": host,
                "pane_id": pane,
                "session_id": session,
                "owner": owner,
                "task": task,
                "fingerprint": fingerprint,
                "state": "dispatching",
                "remote_task_id": None,
                "updated_at": self.clock(),
                "evidence": None,
                "delivery_evidence": None,
                "correlation": f"[dot-fleet:{request_id}]",
                "blocker": None,
            }
            try:
                self.db.execute(
                    "INSERT INTO jobs VALUES (?,?,?,?,?,?)",
                    (request_id, host, pane, session, "dispatching", json.dumps(data)),
                )
            except sqlite3.IntegrityError as error:
                raise ValueError("pane already has an unresolved dispatch") from error
            agent.update(owner=owner, task=task)
            self.db.execute(
                "UPDATE agents SET data=? WHERE host=? AND pane=? AND session=?",
                (json.dumps(agent), host, pane, session),
            )
            return data, True

    def update_job(self, request_id, state, *, reconciled=False, **values):
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            data = self.job(request_id)
            if data is None:
                raise ValueError("unknown request ID")
            if data["state"] in {"completed", "failed", "canceled", "not_submitted"}:
                return data
            if (
                data["state"] == "reported_completed"
                and state != "completed"
                and not reconciled
            ):
                return data
            data.update(values, state=state, updated_at=self.clock())
            self.db.execute(
                "UPDATE jobs SET state=?,data=? WHERE id=?",
                (state, json.dumps(data), request_id),
            )
        return data

    def verify(self, request_id, evidence):
        label(evidence, "independently checked artifact reference")
        job = self.job(request_id)
        if job is None or job["state"] != "reported_completed":
            raise ValueError("only a reported completion can be independently verified")
        return self.update_job(request_id, "completed", evidence=evidence, blocker=None)

    def reconcile(self, request_id, evidence, remote_task_id=None, outcome=None):
        """Explicit operator evidence, never inference from silence or a missing task."""
        label(evidence, "independent reconciliation evidence")
        if bool(remote_task_id) == bool(outcome):
            raise ValueError(
                "choose recovered task ID or independently verified outcome"
            )
        job = self.job(request_id)
        if job is None:
            raise ValueError("unknown request ID")
        if remote_task_id:
            label(remote_task_id, "recovered task ID")
            if job["remote_task_id"] and job["remote_task_id"] != remote_task_id:
                raise ValueError("cannot overwrite an existing remote task identity")
            return self.update_job(
                request_id,
                "dispatched",
                remote_task_id=remote_task_id,
                delivery_evidence=evidence,
                blocker=None,
            )
        if outcome not in {"completed", "failed", "not_submitted"}:
            raise ValueError("invalid reconciliation outcome")
        return self.update_job(
            request_id, outcome, reconciled=True, evidence=evidence, blocker=None
        )

    def event(self, host, envelope, evidence):
        """Existing event consumers invalidate metadata; no new subscription process."""
        label(evidence, "event source reference")
        supported = {
            "pane.created",
            "pane.closed",
            "pane.updated",
            "pane.exited",
            "pane.agent_detected",
            "pane.agent_status_changed",
        }
        lifecycle = {
            "pane_created": "pane.created",
            "pane_closed": "pane.closed",
            "pane_updated": "pane.updated",
            "pane_exited": "pane.exited",
            "pane_agent_detected": "pane.agent_detected",
            "pane_agent_status_changed": "pane.agent_status_changed",
        }
        event = envelope.get("event") if isinstance(envelope, dict) else None
        if not isinstance(event, str) or lifecycle.get(event, event) not in supported:
            raise ValueError("unsupported fleet invalidation event")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            row = self.host(host)
            row.update(
                refresh_required=True, last_event_at=self.clock(), event_source=evidence
            )
            self.db.execute(
                "UPDATE hosts SET data=? WHERE id=?", (json.dumps(row), host)
            )
