"""A self-contained dispatch intent and the readiness/transition rules it needs."""

from dataclasses import dataclass
import hashlib
import json
import re

from .validation import label

TERMINAL = {"completed", "failed", "canceled", "not_submitted"}


@dataclass(frozen=True)
class DispatchIntent:
    request_id: str
    host: str
    pane: str
    session: str
    owner: str
    task: str
    prompt: str

    @property
    def identity(self):
        return self.host, self.pane, self.session

    @property
    def fingerprint(self):
        values = [*self.identity, self.owner, self.task, self.prompt]
        return hashlib.sha256(json.dumps(values).encode()).hexdigest()

    def validate(self):
        for field in ("request_id", "session", "owner", "task"):
            label(getattr(self, field), field)
        if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", self.request_id):
            raise ValueError("request ID must be a simple correlation token")

    def reserved(self, now):
        return {
            "request_id": self.request_id,
            "host_id": self.host,
            "pane_id": self.pane,
            "session_id": self.session,
            "owner": self.owner,
            "task": self.task,
            "fingerprint": self.fingerprint,
            "state": "dispatching",
            "remote_task_id": None,
            "updated_at": now,
            "evidence": None,
            "delivery_evidence": None,
            "correlation": f"[dot-fleet:{self.request_id}]",
            "blocker": None,
        }


def matching_intent(previous, intent):
    if previous["fingerprint"] != intent.fingerprint:
        raise ValueError("request ID already belongs to a different dispatch")
    return previous, False


def require_dispatchable(agent, host, now):
    facts = (
        agent["present"],
        agent["state"] in {"idle", "done"},
        agent["interactive_ready"],
        not agent["launch_pending"],
        agent["source"] == "live",
        0 <= now - agent["last_seen"] <= 30,
        host["observation"] == "reachable",
        not host.get("refresh_required"),
    )
    if not all(facts):
        raise ValueError(
            "dispatch requires a freshly resolved idle or done live session with readiness metadata"
        )
    if "a2a.dispatch" not in agent["capabilities"]:
        raise ValueError("session is not currently in A2A")


def preserves_result(previous, state, reconciled):
    if previous in TERMINAL:
        return True
    return previous == "reported_completed" and state != "completed" and not reconciled


def validate_reconciliation(remote_task_id, outcome):
    if bool(remote_task_id) == bool(outcome):
        raise ValueError("choose recovered task ID or independently verified outcome")
    if remote_task_id:
        label(remote_task_id, "recovered task ID")
        return
    if outcome not in {"completed", "failed", "not_submitted"}:
        raise ValueError("invalid reconciliation outcome")
