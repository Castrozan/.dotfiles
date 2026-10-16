"""Confirmed transport identities and observation failures/events."""

import json

from .validation import label, validate_transport

EVENTS = {
    "pane.created",
    "pane.closed",
    "pane.updated",
    "pane.exited",
    "pane.agent_detected",
    "pane.agent_status_changed",
}
LIFECYCLE_EVENTS = {
    "pane_created": "pane.created",
    "pane_closed": "pane.closed",
    "pane_updated": "pane.updated",
    "pane_exited": "pane.exited",
    "pane_agent_detected": "pane.agent_detected",
    "pane_agent_status_changed": "pane.agent_status_changed",
}


def host(db, host_id):
    row = db.execute("SELECT data FROM hosts WHERE id=?", (host_id,)).fetchone()
    if row is None:
        raise ValueError("unconfirmed host; register reviewed host evidence first")
    return json.loads(row[0])


def save(db, host_id, data):
    db.execute("UPDATE hosts SET data=? WHERE id=?", (json.dumps(data), host_id))


def confirm(db, clock, host_id, transport, evidence):
    label(host_id, "host ID")
    label(evidence, "confirmation evidence reference")
    validate_transport(transport)
    with db:
        db.execute("BEGIN IMMEDIATE")
        previous = db.execute(
            "SELECT data FROM hosts WHERE id=?", (host_id,)
        ).fetchone()
        if previous:
            validate_mapping(json.loads(previous[0]), transport)
            return
        data = {
            "host_id": host_id,
            "transport": transport,
            "confirmation": evidence,
            "confirmed_at": clock(),
            "last_seen": None,
            "last_attempt": None,
            "observation": "unknown",
            "blocker": None,
            "refresh_required": False,
        }
        db.execute("INSERT INTO hosts VALUES (?,?)", (host_id, json.dumps(data)))


def validate_mapping(previous, transport):
    if previous["transport"] != transport:
        raise ValueError("host identity cannot be silently remapped")


def failure(db, clock, host_id, kind):
    if kind not in {"unreachable", "failed"}:
        raise ValueError("invalid observation failure")
    with db:
        db.execute("BEGIN IMMEDIATE")
        row = host(db, host_id)
        row.update(last_attempt=clock(), observation=kind, blocker=kind)
        save(db, host_id, row)


def event(db, clock, host_id, envelope, evidence):
    label(evidence, "event source reference")
    validate_event(envelope)
    with db:
        db.execute("BEGIN IMMEDIATE")
        row = host(db, host_id)
        row.update(refresh_required=True, last_event_at=clock(), event_source=evidence)
        save(db, host_id, row)


def validate_event(envelope):
    name = envelope.get("event") if isinstance(envelope, dict) else None
    if not isinstance(name, str):
        raise ValueError("unsupported fleet invalidation event")
    if LIFECYCLE_EVENTS.get(name, name) not in EVENTS:
        raise ValueError("unsupported fleet invalidation event")
