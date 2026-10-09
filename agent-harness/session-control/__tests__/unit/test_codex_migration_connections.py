import socket
import tempfile
from pathlib import Path

import pytest

from codex_migration_process_fixture import inspect_runtime


def set_client_endpoint(inspection, endpoint):
    arguments = inspection.information["foreground_processes"][1]["argv"]
    arguments[2] = endpoint
    (inspection.directory / "proc/32/cmdline").write_bytes(
        "\0".join(arguments).encode() + b"\0"
    )


@pytest.mark.parametrize("profile_enabled", [False, True])
def test_client_uses_existing_direct_or_profile_proxy_socket(
    process_inspection, monkeypatch, profile_enabled
):
    modules = (
        Path(__file__).resolve().parents[3] / "harnesses/codex/scripts/session_server"
    )
    monkeypatch.syspath_prepend(str(modules))
    from profile_connection import profile_connection_path

    server_path = process_inspection.socket_directory / "server.sock"
    profile_path = process_inspection.directory / "profile.toml"
    profile_path.write_text("model = 'fixture'\n")
    with profile_connection_path(
        server_path, profile_path if profile_enabled else None
    ) as path:
        set_client_endpoint(process_inspection, "unix://" + str(path))
        proof = inspect_runtime(process_inspection)
        assert proof["client_socket"] == str(path.resolve())
        assert proof["server_socket"] == str(server_path.resolve())
        assert path.name == ("client.sock" if profile_enabled else "server.sock")


@pytest.mark.parametrize(
    "endpoint", ["ws://127.0.0.1/fixture", "http://127.0.0.1/fixture"]
)
def test_client_tcp_endpoint_is_refused(process_inspection, endpoint):
    set_client_endpoint(process_inspection, endpoint)
    with pytest.raises(ValueError, match="client"):
        inspect_runtime(process_inspection)


def test_existing_socket_in_another_directory_is_refused(process_inspection):
    with tempfile.TemporaryDirectory(
        prefix="codex-session-other-", dir="/tmp"
    ) as directory:
        path = Path(directory) / "server.sock"
        with socket.socket(socket.AF_UNIX) as unrelated_server:
            unrelated_server.bind(str(path))
            set_client_endpoint(process_inspection, "unix://" + str(path))
            with pytest.raises(ValueError, match="client"):
                inspect_runtime(process_inspection)


def test_missing_profile_socket_is_refused(process_inspection):
    set_client_endpoint(
        process_inspection,
        "unix://" + str(process_inspection.socket_directory / "client.sock"),
    )
    with pytest.raises(ValueError, match="client"):
        inspect_runtime(process_inspection)


def test_undeclared_socket_name_is_refused(process_inspection):
    path = process_inspection.socket_directory / "unrelated.sock"
    with socket.socket(socket.AF_UNIX) as unrelated_server:
        unrelated_server.bind(str(path))
        set_client_endpoint(process_inspection, "unix://" + str(path))
        with pytest.raises(ValueError, match="client"):
            inspect_runtime(process_inspection)


def test_client_argv_changed_since_foreground_observation_is_refused(
    process_inspection,
):
    set_client_endpoint(
        process_inspection,
        "unix://" + str(process_inspection.socket_directory / "server.sock"),
    )
    arguments = list(process_inspection.information["foreground_processes"][1]["argv"])
    arguments[2] = "ws://127.0.0.1/changed"
    (process_inspection.directory / "proc/32/cmdline").write_bytes(
        "\0".join(arguments).encode() + b"\0"
    )
    with pytest.raises(ValueError, match="client"):
        inspect_runtime(process_inspection)
