import json
import os
import subprocess
import sys
import tarfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

import pytest

from agent_api.contract import OperationRequest
from agent_api.inventory import INVENTORY_VARIABLE
from agent_api.service import CapabilityService

JOB_CLI = Path(__file__).resolve().parents[2] / "scripts" / "agent_api_job_cli.py"
MAXIMUM_STATUS_POLLS = 100
POLL_INTERVAL_SECONDS = 0.2
GIT_TIMEOUT_SECONDS = 30

SSH_SHIM = """#!/bin/sh
while [ "$1" = "-o" ]; do shift 2; done
shift 2
exec sh -c "$1"
"""


@pytest.fixture
def second_host(tmp_path, monkeypatch):
    shims = tmp_path / "shims"
    shims.mkdir()
    (shims / "ssh").write_text(SSH_SHIM)
    (shims / "agent-api-job").write_text(
        f'#!/bin/sh\nexec "{sys.executable}" "{JOB_CLI}" "$@"\n'
    )
    for shim in shims.iterdir():
        shim.chmod(0o700)
    inventory = tmp_path / "inventory.json"
    inventory.write_text(
        json.dumps({"self": "chise", "hosts": [{"name": "alpha", "trust": "owned"}]})
    )
    monkeypatch.setenv(INVENTORY_VARIABLE, str(inventory))
    monkeypatch.setenv("AGENT_API_JOB_STATE", str(tmp_path / "job-state"))
    monkeypatch.setenv("PATH", f"{shims}:{os.environ['PATH']}")


@pytest.fixture
def repository(tmp_path):
    directory = tmp_path / "repository"
    directory.mkdir()
    (directory / ".gitignore").write_text("ignored.txt\n")
    for name in ("tracked.txt", "untracked.txt", "ignored.txt"):
        (directory / name).write_text(name)
    subprocess.run(
        ["git", "-C", str(directory), "init", "--quiet"],
        check=True,
        timeout=GIT_TIMEOUT_SECONDS,
    )
    subprocess.run(
        ["git", "-C", str(directory), "add", "tracked.txt"],
        check=True,
        timeout=GIT_TIMEOUT_SECONDS,
    )
    return directory


def run_capability(service, capability, capability_input, operation_id=None):
    receipt = service.run(
        operation_id or str(uuid.uuid4()),
        OperationRequest(capability, capability_input),
    )
    return receipt["result"]["output"]


@contextmanager
def finished_job(service, command, directory):
    job = run_capability(
        service,
        "compute.submit",
        {"command": command, "host": "alpha", "directory": str(directory)},
    )["job"]
    try:
        for _ in range(MAXIMUM_STATUS_POLLS):
            if run_capability(service, "compute.status", {"job": job})["state"] != (
                "running"
            ):
                break
            time.sleep(POLL_INTERVAL_SECONDS)
        yield job
    finally:
        run_capability(service, "compute.cancel", {"job": job})


def test_copying_a_tree_leaves_out_files_git_ignores(tmp_path, second_host, repository):
    service = CapabilityService(tmp_path / "state")
    with finished_job(service, ["ls"], repository) as job:
        logs = run_capability(service, "compute.logs", {"job": job})
    listed = set(logs["log"].splitlines())
    assert listed & {"tracked.txt", "untracked.txt", "ignored.txt"} == {
        "tracked.txt",
        "untracked.txt",
    }


def test_fetch_returns_a_file_the_job_wrote(tmp_path, second_host, repository):
    service = CapabilityService(tmp_path / "state")
    fetch_id = str(uuid.uuid4())
    with finished_job(
        service, ["sh", "-c", "printf written > out.txt"], repository
    ) as job:
        fetched = run_capability(
            service, "compute.fetch", {"job": job, "relative_path": "out.txt"}, fetch_id
        )
    assert fetched["artifact"] == "fetch.tar"
    with tarfile.open(tmp_path / "state" / fetch_id / "fetch.tar") as archive:
        assert archive.extractfile("out.txt").read() == b"written"
