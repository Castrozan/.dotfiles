"""Bounded cached projection; no network activity or inferred task completion."""

import json

COLLECTION_QUERIES = {
    "hosts": "SELECT data FROM hosts ORDER BY id LIMIT ?",
    "agents": "SELECT data FROM agents ORDER BY json_extract(data, '$.present') DESC, host,pane,session LIMIT ?",
    "jobs": "SELECT data FROM jobs ORDER BY json_extract(data, '$.updated_at') DESC,id LIMIT ?",
}
COUNT_QUERIES = {
    "hosts": "SELECT count(*) FROM hosts",
    "agents": "SELECT count(*) FROM agents",
    "jobs": "SELECT count(*) FROM jobs",
}


def evidence_view(row, now, live_hosts, invalidated, freshness):
    last = row["last_seen"]
    row["age_seconds"] = None if last is None else max(0, now - last)
    row["refresh_required"] = row["host_id"] in invalidated
    row["fresh"] = is_fresh(last, now, freshness) and not row["refresh_required"]
    row["view"] = "live" if is_live(row, live_hosts) else "cached"


def is_fresh(last, now, freshness):
    return last is not None and 0 <= now - last <= freshness


def is_live(row, live_hosts):
    return row["host_id"] in live_hosts and row.get("present", True)


def status(db, now, live_hosts, freshness, limit):
    if not 1 <= limit <= 1000:
        raise ValueError("status limit must be between 1 and 1000")
    collections = {
        name: [json.loads(r[0]) for r in db.execute(query, (limit,))]
        for name, query in COLLECTION_QUERIES.items()
    }
    invalidated = {
        row["host_id"] for row in collections["hosts"] if row.get("refresh_required")
    }
    for row in collections["hosts"] + collections["agents"]:
        evidence_view(row, now, live_hosts, invalidated, freshness)
    counts = {
        name: db.execute(query).fetchone()[0] for name, query in COUNT_QUERIES.items()
    }
    return {
        "schema_version": 1,
        "limit": limit,
        "counts": counts,
        "as_of": now,
        **collections,
    }
