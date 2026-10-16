"""Bounded fleet refresh, dispatch and result workflows."""

import json
import time

from .job_intents import TERMINAL
from .session_records import Observation
from .transport import ObservationError as ObservationError
from .transport import command_argv as command_argv
from .transport import remaining_time, run as run
from .validation import label

MAX_HOSTS = 4
REMOTE_STATES = {
    "submitted": "dispatched",
    "working": "working",
    "input_required": "blocked",
    "completed": "reported_completed",
    "failed": "failed",
    "canceled": "canceled",
}


def query(host, command, runner, deadline):
    return json.loads(runner(host, command, timeout=min(5, remaining_time(deadline))))


def refresh_one(registry, host_id, runner, deadline):
    host = registry.host(host_id)
    try:
        directory = query(host, ["a2a", "list", "--json"], runner, deadline)
        snapshot = query(host, ["herdr", "api", "snapshot"], runner, deadline)
        observation = Observation(
            directory,
            snapshot,
            registry.clock(),
            "a2a list + herdr api snapshot",
            "live",
        )
        return registry.ingest(host_id, observation)
    except ObservationError as error:
        registry.failure(host_id, error.kind)
    except (ValueError, TypeError, AttributeError):
        registry.failure(host_id, "failed")
    return False


def validate_hosts(registry, hosts):
    if not hosts or len(hosts) > MAX_HOSTS or len(set(hosts)) != len(hosts):
        raise ValueError(f"select one to {MAX_HOSTS} distinct confirmed hosts")
    for host in hosts:
        registry.host(host)


def refresh(registry, hosts, runner=run, budget=30):
    validate_hosts(registry, hosts)
    deadline = time.monotonic() + budget
    return [host for host in hosts if refresh_one(registry, host, runner, deadline)]


def dispatch(registry, intent, runner=run):
    label(intent.prompt, "single-line prompt")
    if registry.job(intent.request_id):
        return registry.reserve(intent)[0]
    if intent.host not in refresh(registry, [intent.host], runner):
        raise ValueError("live preflight failed; no task submitted")
    job, created = registry.reserve(intent)
    if not created:
        return job
    return send_reserved(registry, intent, job, runner)


def send_reserved(registry, intent, job, runner):
    try:
        receipt = runner(
            registry.host(intent.host),
            [
                "a2a",
                "send",
                intent.pane,
                f"{job['correlation']} {intent.prompt}",
                "--sender",
                intent.owner,
            ],
            timeout=10,
        ).strip()
        label(receipt, "remote task ID")
    except (ObservationError, ValueError):
        return registry.update_job(
            intent.request_id, "uncertain", blocker="receipt_missing_do_not_retry"
        )
    return registry.update_job(intent.request_id, "dispatched", remote_task_id=receipt)


def validate_result_job(registry, request_id):
    job = registry.job(request_id)
    if job is None:
        raise ValueError("unknown request ID")
    if job["state"] in TERMINAL | {"reported_completed"}:
        return job, True
    if not job["remote_task_id"]:
        raise ValueError("no receipt; reconcile target evidence manually, never resend")
    return job, False


def unavailable(registry, job):
    return registry.update_job(
        job["request_id"], job["state"], blocker="status_unavailable"
    )


def fetch_result(registry, job, runner):
    document = json.loads(
        runner(
            registry.host(job["host_id"]),
            ["a2a", "status", job["pane_id"], job["remote_task_id"]],
            timeout=10,
        )
    )
    if not isinstance(document, dict) or document.get("id") != job["remote_task_id"]:
        raise ValueError("task identity mismatch")
    return REMOTE_STATES[document["state"]], document


def result_blocker(state, document):
    if state == "failed":
        error = document.get("errorMessage")
        if isinstance(error, str) and "composer_occupied_or_unrecognized" in error:
            return "composer_occupied_or_unrecognized"
        return "remote_task_failed"
    return {
        "reported_completed": "verify_artifact_and_session",
        "blocked": "peer_requires_input",
    }.get(state)


def read_result(registry, job, runner):
    try:
        state, document = fetch_result(registry, job, runner)
    except (ObservationError, ValueError, KeyError, TypeError):
        return unavailable(registry, job)
    return registry.update_job(
        job["request_id"], state, blocker=result_blocker(state, document)
    )


def result(registry, request_id, runner=run):
    job, finished = validate_result_job(registry, request_id)
    if finished:
        return job
    host = job["host_id"]
    if host not in refresh(registry, [host], runner):
        return unavailable(registry, job)
    agent = registry.agent(host, job["pane_id"], job["session_id"])
    if not agent["present"]:
        return registry.update_job(
            request_id, "uncertain", blocker="session_identity_changed"
        )
    return read_result(registry, job, runner)
