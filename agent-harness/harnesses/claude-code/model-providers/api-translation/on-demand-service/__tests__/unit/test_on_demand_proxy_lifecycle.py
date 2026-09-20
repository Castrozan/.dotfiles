import importlib.util
import os
import socket
import sys
from pathlib import Path

SCRIPTS_DIRECTORY = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIRECTORY))
LIFECYCLE_PATH = SCRIPTS_DIRECTORY / "on_demand_proxy_lifecycle.py"
LIFECYCLE_SPECIFICATION = importlib.util.spec_from_file_location(
    "on_demand_proxy_lifecycle", LIFECYCLE_PATH
)
assert LIFECYCLE_SPECIFICATION
assert LIFECYCLE_SPECIFICATION.loader
LIFECYCLE = importlib.util.module_from_spec(LIFECYCLE_SPECIFICATION)
LIFECYCLE_SPECIFICATION.loader.exec_module(LIFECYCLE)

import holder_registry as REGISTRY

START_COMMAND = ["start-the-proxy"]
STOP_COMMAND = ["stop-the-proxy"]


class RecordedServiceCommands:
    def __init__(self):
        self.commands = []

    def __call__(self, command):
        self.commands.append(list(command))


def listening_socket():
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(4)
    return server


def closed_loopback_port() -> int:
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    return port


def test_the_first_launcher_starts_a_proxy_that_is_not_listening(tmp_path, monkeypatch):
    recorded = RecordedServiceCommands()
    monkeypatch.setattr(LIFECYCLE, "run_service_command", recorded)

    LIFECYCLE.acquire_service(
        tmp_path, "127.0.0.1", closed_loopback_port(), START_COMMAND
    )

    assert recorded.commands == [START_COMMAND]


def test_the_last_launcher_stops_the_proxy_it_started(tmp_path, monkeypatch):
    recorded = RecordedServiceCommands()
    monkeypatch.setattr(LIFECYCLE, "run_service_command", recorded)

    LIFECYCLE.acquire_service(
        tmp_path, "127.0.0.1", closed_loopback_port(), START_COMMAND
    )
    LIFECYCLE.release_service(tmp_path, STOP_COMMAND)

    assert recorded.commands == [START_COMMAND, STOP_COMMAND]


def test_a_proxy_already_listening_is_adopted_and_left_running(tmp_path, monkeypatch):
    recorded = RecordedServiceCommands()
    monkeypatch.setattr(LIFECYCLE, "run_service_command", recorded)

    with listening_socket() as server:
        LIFECYCLE.acquire_service(
            tmp_path, "127.0.0.1", server.getsockname()[1], START_COMMAND
        )
        LIFECYCLE.release_service(tmp_path, STOP_COMMAND)

    assert recorded.commands == [], (
        "a proxy the user started by hand outlives the launcher, so stopping it "
        "would kill a service this launcher never owned"
    )


def test_a_second_live_launcher_keeps_the_proxy_running(tmp_path, monkeypatch):
    recorded = RecordedServiceCommands()
    monkeypatch.setattr(LIFECYCLE, "run_service_command", recorded)

    LIFECYCLE.acquire_service(
        tmp_path, "127.0.0.1", closed_loopback_port(), START_COMMAND
    )
    registry = REGISTRY.HolderRegistry(tmp_path)
    with registry:
        registry.write_holders([os.getpid(), os.getppid()])

    LIFECYCLE.release_service(tmp_path, STOP_COMMAND)

    assert recorded.commands == [START_COMMAND], (
        "a concurrent claudex session still needs the proxy, so releasing one "
        "holder must not stop it under the other"
    )


def test_a_crashed_launcher_does_not_pin_the_proxy_open(tmp_path, monkeypatch):
    recorded = RecordedServiceCommands()
    monkeypatch.setattr(LIFECYCLE, "run_service_command", recorded)

    registry = REGISTRY.HolderRegistry(tmp_path)
    with registry:
        registry.write_holders([unused_process_id()])

    LIFECYCLE.acquire_service(
        tmp_path, "127.0.0.1", closed_loopback_port(), START_COMMAND
    )
    LIFECYCLE.release_service(tmp_path, STOP_COMMAND)

    assert recorded.commands == [START_COMMAND, STOP_COMMAND], (
        "a launcher killed with SIGKILL never releases its holder entry, so stale "
        "entries must not keep the proxy alive forever"
    )


def unused_process_id() -> int:
    candidate = 2**22 - 1
    while REGISTRY.process_is_alive(candidate):
        candidate -= 1
    return candidate


def test_the_child_exit_code_reaches_the_caller(tmp_path, monkeypatch):
    monkeypatch.setattr(LIFECYCLE, "run_service_command", RecordedServiceCommands())

    exit_code = LIFECYCLE.run_with_on_demand_service(
        tmp_path,
        "127.0.0.1",
        closed_loopback_port(),
        START_COMMAND,
        STOP_COMMAND,
        0.0,
        "the proxy never came up",
        ["sh", "-c", "exit 37"],
    )

    assert exit_code == 37


def test_a_proxy_that_never_comes_up_warns_and_still_runs_the_child(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(LIFECYCLE, "run_service_command", RecordedServiceCommands())

    exit_code = LIFECYCLE.run_with_on_demand_service(
        tmp_path,
        "127.0.0.1",
        closed_loopback_port(),
        START_COMMAND,
        STOP_COMMAND,
        0.0,
        "the proxy never came up",
        ["sh", "-c", "exit 0"],
    )

    assert exit_code == 0
    assert "the proxy never came up" in capsys.readouterr().err, (
        "the launcher must say why requests will fail rather than drop the user "
        "into a session that cannot reach any model"
    )
