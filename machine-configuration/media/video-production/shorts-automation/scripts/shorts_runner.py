import fcntl
import os
import signal
import subprocess
from datetime import datetime
from pathlib import Path
from typing import NamedTuple
from zoneinfo import ZoneInfo

from shorts_browser import browser_instance
from shorts_store import (
    RUN_STATUS_FILENAME,
    TopicStore,
    read_document,
    timestamp,
    write_document,
)


class SlotClaim(NamedTuple):
    directory: Path | None
    skipped: dict | None


def publisher_matches(publisher, configuration):
    return publisher.get("status") == "ready" and all(
        publisher.get(field) == configuration[field]
        for field in ("channel_id", "browser_profile", "browser_profile_id")
    )


def publisher_readiness(root, configuration):
    readiness = root / "publisher-ready.json"
    publisher = read_document(readiness) if readiness.is_file() else {}
    if not publisher_matches(publisher, configuration):
        return "Publisher setup is not verified"
    try:
        browser_instance(configuration)
    except (ValueError, subprocess.TimeoutExpired) as error:
        return str(error)
    return None


def claim_slot(root, slot, configuration):
    now = datetime.now(ZoneInfo(configuration["timezone"]))
    selected = slot or now.hour
    if selected not in configuration["hours"]:
        return SlotClaim(
            None, {"status": "skipped", "reason": "Outside scheduled production slots"}
        )
    identifier = f"{now.date()}-{selected:02d}00"
    directory = root / "runs" / identifier
    if directory.exists():
        return SlotClaim(
            None,
            {
                "status": "skipped",
                "reason": "Slot already claimed",
                "run_id": identifier,
            },
        )
    directory.mkdir(parents=True, mode=0o700)
    write_document(directory / "history.json", TopicStore(root).history())
    write_document(directory / "config.json", configuration)
    write_document(
        directory / RUN_STATUS_FILENAME,
        {"status": "started", "started_at": timestamp()},
    )
    return SlotClaim(directory, None)


def agent_arguments(directory, configuration):
    return [
        os.environ["SHORTS_CODEX"],
        "exec",
        "--skip-git-repo-check",
        "-C",
        str(directory),
        "--model",
        configuration["model"],
        "-c",
        'model_reasoning_effort="high"',
        "-c",
        'web_search="live"',
        "-c",
        'plugins."betha-chrome-devtools@betha-agent-marketplace".mcp_servers.chrome-devtools.enabled=false',
        "-c",
        'plugins."betha-desenvolvimento@betha-agent-marketplace".mcp_servers.chrome-devtools.enabled=false',
        "-c",
        'approval_policy="never"',
        "--sandbox",
        "danger-full-access",
        "--json",
        "--output-last-message",
        str(directory / "agent-result.txt"),
        "--",
        Path(os.environ["SHORTS_GOAL_PROMPT"]).read_text().strip(),
    ]


def execute_agent(directory, configuration):
    with (directory / "agent-events.jsonl").open("w") as output:
        process = subprocess.Popen(
            agent_arguments(directory, configuration),
            stdout=output,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env=dict(os.environ, CLAWDE_AGENT_NAME="shorts-production"),
        )
        try:
            returncode = process.wait(timeout=7200)
            return "agent_finished" if returncode == 0 else "needs_inspection"
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            return "needs_inspection"


def finish_run(directory, status):
    previous = read_document(directory / RUN_STATUS_FILENAME)
    if previous["status"] == "published":
        return previous
    if (directory / "hold.json").is_file():
        status = "held"
    previous.update(status=status, finished_at=timestamp())
    write_document(directory / RUN_STATUS_FILENAME, previous)
    return previous


def start_run(root, slot, configuration):
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    reason = publisher_readiness(root, configuration)
    if reason:
        return {"status": "skipped", "reason": reason}
    with (root / "production.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {"status": "skipped", "reason": "Another production run is active"}
        claim = claim_slot(root, slot, configuration)
        if claim.directory is None:
            return claim.skipped
        return finish_run(
            claim.directory, execute_agent(claim.directory, configuration)
        )
