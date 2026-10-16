"""Durable reservation, receipt and independently attested result transactions."""

import json
import sqlite3

from . import host_records, session_records
from .job_intents import (
    matching_intent,
    preserves_result,
    require_dispatchable,
    validate_reconciliation,
)
from .validation import label


def job(db, request_id):
    row = db.execute("SELECT data FROM jobs WHERE id=?", (request_id,)).fetchone()
    return json.loads(row[0]) if row else None


def required_job(db, request_id):
    data = job(db, request_id)
    if data is None:
        raise ValueError("unknown request ID")
    return data


def insert_reservation(db, intent, data):
    try:
        db.execute(
            "INSERT INTO jobs VALUES (?,?,?,?,?,?)",
            (intent.request_id, *intent.identity, "dispatching", json.dumps(data)),
        )
    except sqlite3.IntegrityError as error:
        raise ValueError("pane already has an unresolved dispatch") from error


def reserve(db, clock, intent):
    intent.validate()
    with db:
        db.execute("BEGIN IMMEDIATE")
        previous = job(db, intent.request_id)
        if previous:
            return matching_intent(previous, intent)
        agent = session_records.agent(db, *intent.identity)
        host = host_records.host(db, intent.host)
        require_dispatchable(agent, host, clock())
        data = intent.reserved(clock())
        insert_reservation(db, intent, data)
        agent.update(owner=intent.owner, task=intent.task)
        session_records.save(db, intent.identity, agent)
        return data, True


def update(db, clock, request_id, state, values):
    with db:
        db.execute("BEGIN IMMEDIATE")
        data = required_job(db, request_id)
        reconciled = values.pop("reconciled", False)
        if preserves_result(data["state"], state, reconciled):
            return data
        data.update(values, state=state, updated_at=clock())
        db.execute(
            "UPDATE jobs SET state=?,data=? WHERE id=?",
            (state, json.dumps(data), request_id),
        )
    return data


def verify(db, clock, request_id, evidence):
    label(evidence, "independently checked artifact reference")
    record = job(db, request_id)
    if record is None or record["state"] != "reported_completed":
        raise ValueError("only a reported completion can be independently verified")
    return update(
        db, clock, request_id, "completed", {"evidence": evidence, "blocker": None}
    )


def recovered_receipt(record, remote_task_id, evidence):
    if record["remote_task_id"] and record["remote_task_id"] != remote_task_id:
        raise ValueError("cannot overwrite an existing remote task identity")
    return "dispatched", {
        "remote_task_id": remote_task_id,
        "delivery_evidence": evidence,
        "blocker": None,
    }


def reconcile(db, clock, request_id, evidence, resolution):
    label(evidence, "independent reconciliation evidence")
    remote_task_id, outcome = resolution
    validate_reconciliation(remote_task_id, outcome)
    record = required_job(db, request_id)
    values = {"reconciled": True, "evidence": evidence, "blocker": None}
    if remote_task_id:
        outcome, values = recovered_receipt(record, remote_task_id, evidence)
    return update(db, clock, request_id, outcome, values)
