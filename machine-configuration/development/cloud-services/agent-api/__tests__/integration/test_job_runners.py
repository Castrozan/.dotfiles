import json
import os
import time
import uuid

import pytest

from agent_api_job.cli import main
from agent_api_job.runners import RUNNERS, user_manager_answers

WAIT_SECONDS = 20
COMMAND_WITH_AWKWARD_ARGUMENTS = [
    "sh",
    "-c",
    "printf '%s\\n' \"$@\"; exit 3",
    "job",
    "$HOME",
    "%h",
    "two words",
]


def wait_for(produce):
    deadline = time.monotonic() + WAIT_SECONDS
    while time.monotonic() < deadline:
        value = produce()
        if value:
            return value
        time.sleep(0.05)
    raise AssertionError("condition was not met in time")


class JobCommandLine:
    def __init__(self, capsys, jobs):
        self.capsys = capsys
        self.jobs = jobs

    def call(self, arguments, expected_exit=0):
        assert main(arguments) == expected_exit
        captured = self.capsys.readouterr()
        return json.loads(captured.out if expected_exit == 0 else captured.err)

    def start(self, command, runtime_seconds=60):
        job = str(uuid.uuid4())
        self.jobs.append(job)
        return self.call(
            [
                "start",
                job,
                "--memory-megabytes",
                "256",
                "--cpu-percent",
                "100",
                "--runtime-seconds",
                str(runtime_seconds),
                "--",
                *command,
            ]
        ) | {"id": job}

    def status(self, job):
        return self.call(["status", job])

    def finished_status(self, job):
        return wait_for(
            lambda: (status := self.status(job))["state"] != "running" and status
        )


@pytest.fixture(params=["systemd", "supervisor"])
def job_commands(request, tmp_path, monkeypatch, capsys):
    runner = RUNNERS[request.param]
    if request.param == "systemd" and not user_manager_answers():
        pytest.skip("no systemd user manager answers on this machine")
    monkeypatch.setenv("AGENT_API_JOB_STATE", str(tmp_path / "state"))
    monkeypatch.setattr("agent_api_job.cli.select_runner", lambda: runner)
    jobs = []
    yield JobCommandLine(capsys, jobs)
    for job in jobs:
        main(["cancel", job])
    capsys.readouterr()


def test_job_receives_arguments_verbatim_and_reports_exit_code_and_output(
    job_commands,
):
    job = job_commands.start(COMMAND_WITH_AWKWARD_ARGUMENTS)["id"]
    status = job_commands.finished_status(job)
    assert (status["state"], status["exit_code"], status["result"]) == (
        "failed",
        3,
        "exit-code",
    )
    expected = "$HOME\n%h\ntwo words\n"
    wait_for(
        lambda: expected in job_commands.call(["logs", job, "--lines", "50"])["log"]
    )


def test_cancel_stops_a_running_job_and_status_then_reports_unknown(
    job_commands, tmp_path
):
    process_file = tmp_path / "process-id"
    job = job_commands.start(
        ["sh", "-c", 'echo $$ > "$0"; exec sleep 60', str(process_file)]
    )["id"]
    process_id = int(
        wait_for(lambda: process_file.exists() and process_file.read_text())
    )
    assert job_commands.status(job)["state"] == "running"
    assert job_commands.call(["cancel", job])["cancelled"] is True
    assert job_commands.status(job)["state"] == "unknown"

    def process_is_gone():
        try:
            os.kill(process_id, 0)
        except ProcessLookupError:
            return True

    wait_for(process_is_gone)


def test_job_past_its_runtime_limit_is_stopped_and_reported_as_timeout(job_commands):
    job = job_commands.start(["sleep", "60"], runtime_seconds=1)["id"]
    status = job_commands.finished_status(job)
    assert (status["state"], status["result"]) == ("failed", "timeout")
