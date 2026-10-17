import importlib
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest


@pytest.fixture
def supervised_owner(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2]))
    owner = importlib.import_module("opencli_owner")
    connection, controller = socket.socketpair()
    with connection, controller:
        monkeypatch.setattr(owner, "owner_connection", connection)
        yield owner


def stop_startup_processes(process, directory):
    identifiers = [process.pid]
    for name in ("child.pid", "worker.pid"):
        path = directory / name
        if path.exists():
            identifiers.append(int(path.read_text()))
    for identifier in identifiers:
        try:
            os.killpg(identifier, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=5)


def running(identifier):
    result = subprocess.run(
        ["ps", "-o", "stat=", "-p", str(identifier)],
        capture_output=True,
        text=True,
        timeout=5,
    )
    return result.returncode == 0 and not result.stdout.strip().startswith("Z")


@pytest.mark.parametrize("scenario", ["worker", "client"])
def test_startup_interruption_cannot_leave_an_unregistered_child(tmp_path, scenario):
    fixture = Path(__file__).with_name("startup_fixture.py")
    runtime = Path(__file__).resolve().parents[2]
    with (tmp_path / "controller.log").open("w") as output:
        process = subprocess.Popen(
            [
                sys.executable,
                str(fixture),
                "controller",
                scenario,
                str(tmp_path),
                str(runtime),
            ],
            stdout=output,
            stderr=output,
            start_new_session=True,
        )
        try:
            process.wait(timeout=15)
            marker = tmp_path / "child.pid"
            assert marker.exists(), (tmp_path / "controller.log").read_text()
            child = int(marker.read_text())
            deadline = time.monotonic() + 6
            while running(child) and time.monotonic() < deadline:
                time.sleep(0.05)
            assert not running(child), "An owned child survived its startup controller"
        finally:
            stop_startup_processes(process, tmp_path)


def test_owned_program_receives_original_signal_mask(supervised_owner, tmp_path):
    expected = sorted(
        int(number) for number in signal.pthread_sigmask(signal.SIG_BLOCK, [])
    )
    program = "import json,signal; print(json.dumps(sorted(int(number) for number in signal.pthread_sigmask(signal.SIG_BLOCK, []))))"
    path = tmp_path / "signals.json"
    with path.open("w") as output:
        with supervised_owner.owned_process(
            [sys.executable, "-c", program], dict(os.environ), output
        ) as process:
            assert process.wait(timeout=5) == 0
    assert json.loads(path.read_text()) == expected


def test_owned_program_retains_native_broken_pipe_behavior(supervised_owner):
    with supervised_owner.owned_process(
        ["/bin/sh", "-c", 'kill -PIPE "$$"; exit 9'], dict(os.environ)
    ) as process:
        assert process.wait(timeout=5) == -signal.SIGPIPE
