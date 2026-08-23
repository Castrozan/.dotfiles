from __future__ import annotations

import socket
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

APPLICATION_LAUNCHER_CLIENT_SCRIPT = (
    Path(__file__).resolve().parents[2] / "scripts" / "application_launcher_client.py"
)


@pytest.fixture
def short_lived_directory():
    with tempfile.TemporaryDirectory(prefix="al") as directory:
        yield Path(directory)


@pytest.fixture
def bound_daemon_socket(short_lived_directory):
    daemon_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    daemon_socket.bind(str(short_lived_directory / "daemon.sock"))
    daemon_socket.settimeout(5)
    yield daemon_socket
    daemon_socket.close()


def run_client(daemon_socket_path):
    return subprocess.run(
        [
            sys.executable,
            str(APPLICATION_LAUNCHER_CLIENT_SCRIPT),
            str(daemon_socket_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_sends_the_show_datagram_to_the_daemon_socket(
    bound_daemon_socket, short_lived_directory
):
    completed = run_client(short_lived_directory / "daemon.sock")

    assert bound_daemon_socket.recv(64) == b"show"
    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_reports_the_socket_error_and_exits_one(short_lived_directory):
    completed = run_client(short_lived_directory / "nothing-is-listening.sock")

    assert completed.returncode == 1
    assert completed.stdout == ""
    assert completed.stderr.startswith("application-launcher: ")
    assert completed.stderr.endswith("\n")
