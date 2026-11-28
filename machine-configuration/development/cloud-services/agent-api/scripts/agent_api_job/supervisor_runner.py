import fcntl
import os
import signal
import sys
import time
from pathlib import Path

from agent_api_job.detach import spawn_detached
from agent_api_job.errors import JobError
from agent_api_job.model import (
    CANCEL_MARKER,
    LOCK_FILE,
    MAXIMUM_LOG_CHARACTERS,
    job_outcome,
)
from agent_api_job.storage import read_json
from agent_api_job.supervisor import signal_group

START_TIMEOUT_SECONDS = 10
START_POLL_SECONDS = 0.02
ENTRY_SCRIPT = Path(__file__).resolve().parents[1] / "agent_api_job_cli.py"


def await_started(job_directory):
    deadline = time.monotonic() + START_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if any(
            (job_directory / name).exists() for name in ("process.json", "exit.json")
        ):
            return
        time.sleep(START_POLL_SECONDS)
    raise JobError("start_failed")


def supervisor_running(job):
    try:
        descriptor = os.open(job.directory / LOCK_FILE, os.O_RDONLY)
    except FileNotFoundError:
        return False
    try:
        fcntl.flock(descriptor, fcntl.LOCK_SH | fcntl.LOCK_NB)
    except BlockingIOError:
        return True
    finally:
        os.close(descriptor)
    return False


class SupervisorRunner:
    name = "supervisor"
    limits_enforced = ["runtime_seconds"]

    def start(self, job, limits, command):
        try:
            spawn_detached(
                [
                    sys.executable,
                    str(ENTRY_SCRIPT),
                    "supervise",
                    str(job.directory),
                    str(job.working_directory),
                    str(limits.runtime_seconds),
                    "--",
                    *command,
                ]
            )
        except OSError:
            raise JobError("start_failed") from None
        await_started(job.directory)

    def status(self, job):
        if (job.directory / CANCEL_MARKER).exists():
            return job_outcome("unknown")
        running = supervisor_running(job)
        outcome = read_json(job.directory / "exit.json")
        if outcome:
            state = "succeeded" if outcome["result"] == "success" else "failed"
            return job_outcome(state, outcome["exit_code"], outcome["result"])
        return job_outcome("running" if running else "unknown")

    def logs(self, job, lines):
        try:
            with (job.directory / "log").open("rb") as stream:
                size = stream.seek(0, os.SEEK_END)
                stream.seek(max(0, size - MAXIMUM_LOG_CHARACTERS * 4))
                data = stream.read()
        except FileNotFoundError:
            return ""
        text = data.decode(errors="replace")
        return "".join(text.splitlines(keepends=True)[-lines:])[
            -MAXIMUM_LOG_CHARACTERS:
        ]

    def cancel(self, job):
        marker = job.directory / CANCEL_MARKER
        if marker.exists():
            raise JobError("job_not_loaded")
        running = supervisor_running(job)
        process = read_json(job.directory / "process.json")
        marker.touch(mode=0o600)
        if running and process:
            signal_group(process["group"], signal.SIGTERM)
