"""Explicit recovery of inspected held slots; scheduled runs never backfill."""

import fcntl
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from shorts_store import TopicStore, read_document, timestamp, write_document

ACTIONS = ("queue-recovery", "recover-next", "drain-recovery")
QUEUE_FILE = "recovery-queue.json"
RUN_BUDGET_SECONDS = 125 * 60


def recovery_directory(root, identifier, configuration):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}-(09|15|21)00", identifier):
        raise ValueError("Expected an existing scheduled run ID")
    directory = root / "runs" / identifier
    status = read_document(directory / "status.json")
    if status["status"] != "held" or (directory / "publication.json").exists():
        raise ValueError("Recovery requires a held run with no publication dispatch")
    saved = read_document(directory / "config.json")
    if saved != configuration:
        raise ValueError("Recovery configuration differs from the held run")
    episode = read_document(directory / "episode.json")
    TopicStore(root).reservation(identifier, episode["topic_key"])
    return directory


def read_queue(root):
    path = root / QUEUE_FILE
    return read_document(path) if path.exists() else {"runs": []}


def queue_recoveries(root, identifiers, configuration):
    with (root / "production.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        queue = read_queue(root)
        pending = {
            item["run_id"]
            for item in queue["runs"]
            if item["status"] in ("queued", "running")
        }
        if len(pending | set(identifiers)) > 2:
            raise ValueError("Queue at most two explicitly requested recoveries")
        for identifier in identifiers:
            if any(item["run_id"] == identifier for item in queue["runs"]):
                continue
            recovery_directory(root, identifier, configuration)
            queue["runs"].append(
                {"run_id": identifier, "status": "queued", "requested_at": timestamp()}
            )
        write_document(root / QUEUE_FILE, queue)
    return queue


def window_available(configuration, now=None):
    now = now or datetime.now(ZoneInfo(configuration["timezone"]))
    slots = [
        now.replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=day)
        for day in (0, 1)
        for hour in configuration["hours"]
    ]
    next_slot = min(slot for slot in slots if slot > now)
    recent_slot = max((slot for slot in slots if slot <= now), default=None)
    if recent_slot is not None and (now - recent_slot).total_seconds() <= 120:
        return False
    # Leave the full systemd deadline plus one minute of scheduler accuracy.
    return (next_slot - now).total_seconds() > RUN_BUDGET_SECONDS + 60


def archive_attempt(directory):
    attempts = directory / "recovery-attempts"
    attempts.mkdir(exist_ok=True)
    archive = attempts / f"{len(list(attempts.iterdir())) + 1:03d}"
    archive.mkdir()
    for name in ("status.json", "hold.json", "agent-events.jsonl", "agent-result.txt"):
        path = directory / name
        if path.exists():
            shutil.copy2(path, archive / name)
    (directory / "hold.json").unlink(missing_ok=True)
    write_document(
        directory / "status.json",
        {
            "status": "started",
            "started_at": timestamp(),
            "recovery_archive": str(archive.relative_to(directory)),
        },
    )


def recover_next(root, configuration):
    with (root / "production.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {"status": "deferred", "reason": "Another production run is active"}
        queue = read_queue(root)
        item = next(
            (item for item in queue["runs"] if item["status"] == "queued"), None
        )
        if item is None:
            return {"status": "empty"}
        if not window_available(configuration):
            return {
                "status": "deferred",
                "reason": "Reserved time for the next scheduled slot",
            }
        return execute_recovery(root, configuration, queue, item)


def execute_recovery(root, configuration, queue, item):
    import shorts_runner

    try:
        directory = recovery_directory(root, item["run_id"], configuration)
    except (ValueError, OSError) as error:
        item.update(status="needs_inspection", reason=str(error))
        write_document(root / QUEUE_FILE, queue)
        return item
    reason = shorts_runner.publisher_readiness(root, configuration)
    if reason:
        item.update(status="held", reason=reason)
        write_document(root / QUEUE_FILE, queue)
        return item
    item.update(status="running", started_at=timestamp())
    write_document(root / QUEUE_FILE, queue)
    archive_attempt(directory)
    os.environ["SHORTS_GOAL_PROMPT"] = os.environ["SHORTS_RECOVERY_GOAL"]
    try:
        return shorts_runner.execute_run(directory, configuration)
    finally:
        status = read_document(directory / "status.json")
        item.update(status=status["status"], finished_at=timestamp())
        write_document(root / QUEUE_FILE, queue)


def drain_queue(root, configuration):
    while has_unfinished(root):
        launch_pending(root, configuration)
        time.sleep(60)
    return read_queue(root)


def has_unfinished(root):
    return any(
        item["status"] in ("queued", "running") for item in read_queue(root)["runs"]
    )


def launch_pending(root, configuration):
    statuses = {item["status"] for item in read_queue(root)["runs"]}
    if "running" in statuses or "queued" not in statuses:
        return
    if window_available(configuration):
        # A daemon reexec can disconnect a blocking D-Bus wait after accepting a
        # job. Observe the durable queue before another request instead.
        try:
            subprocess.run(
                [
                    "systemctl",
                    "--user",
                    "start",
                    "--no-block",
                    "shorts-recovery.service",
                ],
                check=False,
                timeout=15,
            )
        except subprocess.TimeoutExpired:
            pass


def command(arguments, root, configuration):
    if arguments.action == "queue-recovery":
        return queue_recoveries(root, arguments.run_id, configuration)
    operation = {"recover-next": recover_next, "drain-recovery": drain_queue}[
        arguments.action
    ]
    return operation(root, configuration)
