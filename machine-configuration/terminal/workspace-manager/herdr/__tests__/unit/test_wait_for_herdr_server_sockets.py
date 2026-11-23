import errno
import importlib.util
import pathlib
import socket
import tempfile

import pytest


SCRIPT_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "scripts"
    / "wait-for-herdr-server-sockets.py"
)
module_spec = importlib.util.spec_from_file_location(
    "wait_for_herdr_server_sockets", SCRIPT_PATH
)
server_socket_guard = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(server_socket_guard)


@pytest.fixture
def socket_directory():
    with tempfile.TemporaryDirectory(prefix="herdr-", dir="/tmp") as directory:
        yield pathlib.Path(directory)


@pytest.mark.parametrize("socket_name", ["herdr.sock", "herdr-client.sock"])
def test_either_live_socket_blocks_startup_until_it_closes(
    socket_directory, monkeypatch, socket_name
):
    socket_path = socket_directory / socket_name
    delays = []
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        listener.bind(str(socket_path))
        listener.listen()

        def close_existing_listener(seconds):
            delays.append(seconds)
            listener.close()

        monkeypatch.setattr(server_socket_guard.time, "sleep", close_existing_listener)

        server_socket_guard.wait_for_server_sockets(socket_directory)

    assert delays == [5]
    assert socket_path.exists()


def test_socket_probes_have_a_timeout(tmp_path, monkeypatch):
    timeouts = []

    def record_connection_timeout(connection, address):
        timeouts.append(connection.gettimeout())
        raise FileNotFoundError(errno.ENOENT, "missing")

    monkeypatch.setattr(socket.socket, "connect", record_connection_timeout)

    server_socket_guard.wait_for_server_sockets(tmp_path)

    assert timeouts == [1, 1]
