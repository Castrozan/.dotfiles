"""Apply complete observations atomically, retaining historical identities."""

from dataclasses import dataclass
import json

from . import host_records
from .snapshots import normalize
from .validation import label, validate_timestamp


@dataclass(frozen=True)
class Observation:
    directory: dict
    snapshot: dict
    observed_at: float
    evidence: str
    source: str = "cached"

    def validate(self, now):
        if self.source not in {"live", "cached"}:
            raise ValueError("invalid evidence source")
        label(self.evidence, "evidence reference")
        validate_timestamp(self.observed_at, now)


def agent(db, host, pane, session):
    row = db.execute(
        "SELECT data FROM agents WHERE host=? AND pane=? AND session=?",
        (host, pane, session),
    ).fetchone()
    if row is None:
        raise ValueError("agent/session identity has not been observed")
    return json.loads(row[0])


def save(db, identity, data):
    db.execute(
        "UPDATE agents SET data=? WHERE host=? AND pane=? AND session=?",
        (json.dumps(data), *identity),
    )


def assign(db, identity, owner, task):
    label(owner, "owner")
    label(task, "task reference")
    with db:
        db.execute("BEGIN IMMEDIATE")
        row = agent(db, *identity)
        row.update(owner=owner, task=task)
        save(db, identity, row)


def retire_present(db, host):
    previous = db.execute(
        "SELECT pane,session,data FROM agents WHERE host=? AND json_extract(data, '$.present')=1",
        (host,),
    ).fetchall()
    for record in previous:
        data = json.loads(record["data"])
        data["present"] = False
        save(db, (host, record["pane"], record["session"]), data)


def save_observation(db, host, row, observation):
    session = row["session_id"] or ""
    previous = db.execute(
        "SELECT data FROM agents WHERE host=? AND pane=? AND session=?",
        (host, row["pane_id"], session),
    ).fetchone()
    owned = json.loads(previous[0]) if previous else {}
    row.update(
        host_id=host,
        present=True,
        last_seen=observation.observed_at,
        source=observation.source,
        evidence=observation.evidence,
        owner=owned.get("owner"),
        task=owned.get("task"),
    )
    db.execute(
        "INSERT OR REPLACE INTO agents VALUES (?,?,?,?)",
        (host, row["pane_id"], session, json.dumps(row)),
    )


def ingest(db, clock, host, observation):
    observation.validate(clock())
    rows = normalize(observation.directory, observation.snapshot)
    with db:
        db.execute("BEGIN IMMEDIATE")
        record = host_records.host(db, host)
        if is_older(record, observation):
            return False
        retire_present(db, host)
        for row in rows:
            save_observation(db, host, row, observation)
        record.update(
            last_seen=observation.observed_at,
            last_attempt=clock(),
            observation="reachable",
            blocker=None,
            refresh_required=False,
        )
        host_records.save(db, host, record)
    return True


def is_older(host, observation):
    return (
        host["last_seen"] is not None and observation.observed_at <= host["last_seen"]
    )
