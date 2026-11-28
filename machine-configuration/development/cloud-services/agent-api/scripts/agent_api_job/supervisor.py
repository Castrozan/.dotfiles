import os
import signal
import subprocess
import time
from contextlib import suppress

from agent_api_job.model import CANCEL_MARKER
from agent_api_job.storage import write_json

POLL_SECONDS = 0.2
TERMINATION_GRACE_SECONDS = 5
COMMAND_NOT_RUNNABLE_EXIT_CODE = 127


def signal_group(group, signal_number):
    with suppress(ProcessLookupError, PermissionError):
        os.killpg(group, signal_number)


def stop_group(child):
    signal_group(child.pid, signal.SIGTERM)
    try:
        return child.wait(timeout=TERMINATION_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        signal_group(child.pid, signal.SIGKILL)
        return child.wait()


def wait_for_child(child, job_directory, runtime_seconds):
    deadline = time.monotonic() + runtime_seconds
    while True:
        try:
            return child.wait(timeout=POLL_SECONDS), False
        except subprocess.TimeoutExpired:
            pass
        if time.monotonic() >= deadline:
            return stop_group(child), True
        if (job_directory / CANCEL_MARKER).exists():
            return stop_group(child), False


def outcome_for(return_code, timed_out):
    if timed_out:
        return {"exit_code": abs(return_code), "result": "timeout"}
    if return_code < 0:
        return {"exit_code": -return_code, "result": "signal"}
    result = "success" if return_code == 0 else "exit-code"
    return {"exit_code": return_code, "result": result}


def launch(job_directory, working_directory, command):
    log = os.open(job_directory / "log", os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        return subprocess.Popen(
            command,
            cwd=working_directory,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    except (OSError, ValueError):
        return None
    finally:
        os.close(log)


def supervise(job_directory, working_directory, runtime_seconds, command):
    child = launch(job_directory, working_directory, command)
    if child is None:
        write_json(
            job_directory / "exit.json",
            {"exit_code": COMMAND_NOT_RUNNABLE_EXIT_CODE, "result": "exit-code"},
        )
        return
    write_json(
        job_directory / "process.json", {"supervisor": os.getpid(), "group": child.pid}
    )
    return_code, timed_out = wait_for_child(child, job_directory, runtime_seconds)
    write_json(job_directory / "exit.json", outcome_for(return_code, timed_out))
