import json
from pathlib import Path
import tempfile
import threading
import tomllib

import pytest
from websockets.sync.client import unix_connect
from websockets.sync.server import unix_serve
from websockets.exceptions import ConnectionClosedOK

from profile_connection import profile_connection_path


@pytest.fixture
def socket_directory():
    with tempfile.TemporaryDirectory(
        prefix="codex-profile-test-", dir="/tmp"
    ) as directory:
        yield Path(directory)


def test_profile_connection_relays_large_responses_and_routes_runtime_writes(
    tmp_path, socket_directory
):
    server_path = socket_directory / "server.sock"
    profile_path = tmp_path / "interactive.config.toml"
    profile_path.write_text('model_reasoning_effort = "high"\n')
    received = []

    def handle(connection):
        for frame in connection:
            request = json.loads(frame)
            received.append(request)
            result = (
                {"value": "x" * (1024 * 1024 + 1)}
                if request["method"] == "probe"
                else {"filePath": str(tmp_path / "config.toml")}
            )
            connection.send(json.dumps({"id": request["id"], "result": result}))

    server = unix_serve(handle, str(server_path))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with profile_connection_path(server_path, profile_path) as client_path:
            with unix_connect(
                str(client_path), uri="ws://localhost", max_size=2 * 1024 * 1024
            ) as client:
                client.send('{"id":1,"method":"probe","params":{}}')
                assert (
                    len(json.loads(client.recv(timeout=1))["result"]["value"])
                    > 1024 * 1024
                )
                client.send(
                    '{"id":2,"method":"config/batchWrite","params":{"edits":[{"keyPath":"model_reasoning_effort","value":"medium","mergeStrategy":"upsert"}]}}'
                )
                assert json.loads(client.recv(timeout=1))["result"]["filePath"] == str(
                    profile_path
                )
        assert received[1]["params"]["edits"] == []
        assert (
            tomllib.loads(profile_path.read_text())["model_reasoning_effort"]
            == "medium"
        )
    finally:
        server.shutdown()
        thread.join(timeout=1)


def test_missing_upstream_closes_profile_connection_without_server_error(
    tmp_path, socket_directory
):
    profile_path = tmp_path / "interactive.config.toml"
    profile_path.write_text('model_reasoning_effort = "high"\n')
    with profile_connection_path(
        socket_directory / "missing.sock", profile_path
    ) as client_path:
        with unix_connect(str(client_path), uri="ws://localhost") as client:
            with pytest.raises(ConnectionClosedOK):
                client.recv(timeout=1)


def test_session_without_profile_keeps_native_socket(tmp_path):
    server_path = tmp_path / "native.sock"
    with profile_connection_path(server_path, None) as client_path:
        assert client_path == server_path
    assert not (tmp_path / "client.sock").exists()
