import importlib.util
import json
import pathlib
import subprocess
import sys
from types import SimpleNamespace

import pytest

SCRIPT_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "scripts"
    / "reconcile-herdr-server.py"
)


def _load_module():
    module_spec = importlib.util.spec_from_file_location(
        "reconcile_herdr_server", SCRIPT_PATH
    )
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    return module


reconcile_herdr_server = _load_module()


def _result(returncode=0, payload=None):
    stdout = "" if payload is None else json.dumps(payload)
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr="")


def _set_environment(monkeypatch, tmp_path):
    active_package_file = tmp_path / "active-server-package"
    monkeypatch.setenv("HERDR_EXECUTABLE", "/nix/store/new-herdr/bin/herdr")
    monkeypatch.setenv(
        "HERDR_IMPORT_EXECUTABLE", "/nix/store/importer/bin/herdr-handoff-importer"
    )
    monkeypatch.setenv("HERDR_PACKAGE_IDENTITY", "/nix/store/new-herdr")
    monkeypatch.setenv("HERDR_ACTIVE_PACKAGE_FILE", str(active_package_file))
    return active_package_file


def _running_server(protocol=16, live_handoff=True):
    return {
        "status": "running",
        "running": True,
        "version": "0.7.3",
        "protocol": protocol,
        "capabilities": {"live_handoff": live_handoff},
    }


def _client():
    return {"version": "0.7.3", "protocol": 16}


def test_reconcile_is_no_op_when_desired_package_is_active(monkeypatch, tmp_path):
    active_package_file = _set_environment(monkeypatch, tmp_path)
    active_package_file.write_text("/nix/store/new-herdr\n")
    commands = []
    monkeypatch.setattr(
        reconcile_herdr_server,
        "run_command",
        lambda *arguments, **options: commands.append((arguments, options)),
    )

    reconcile_herdr_server.main(["reconcile"])

    assert commands == []


def test_reconcile_is_no_op_when_server_is_not_running(monkeypatch, tmp_path):
    active_package_file = _set_environment(monkeypatch, tmp_path)
    commands = []

    def run_command(*arguments, **options):
        commands.append((arguments, options))
        return _result(returncode=1)

    monkeypatch.setattr(reconcile_herdr_server, "run_command", run_command)
    reconcile_herdr_server.main(["reconcile"])

    assert [arguments for arguments, _ in commands] == [
        ("/nix/store/new-herdr/bin/herdr", "status", "server", "--json")
    ]
    assert not active_package_file.exists()


def test_changed_package_hands_off_once_and_records_identity(monkeypatch, tmp_path):
    active_package_file = _set_environment(monkeypatch, tmp_path)
    active_package_file.write_text("/nix/store/old-herdr\n")
    commands = []
    results = iter(
        [
            _result(payload=_running_server()),
            _result(payload=_client()),
            _result(),
            _result(payload=_running_server()),
        ]
    )

    def run_command(*arguments, **options):
        commands.append((arguments, options))
        return next(results)

    monkeypatch.setattr(reconcile_herdr_server, "run_command", run_command)
    reconcile_herdr_server.main(["reconcile"])

    assert [arguments for arguments, _ in commands] == [
        ("/nix/store/new-herdr/bin/herdr", "status", "server", "--json"),
        ("/nix/store/new-herdr/bin/herdr", "status", "client", "--json"),
        (
            "/nix/store/new-herdr/bin/herdr",
            "server",
            "live-handoff",
            "--import-exe",
            "/nix/store/importer/bin/herdr-handoff-importer",
            "--expected-protocol",
            "16",
            "--expected-version",
            "0.7.3",
        ),
        ("/nix/store/new-herdr/bin/herdr", "status", "server", "--json"),
    ]
    assert active_package_file.read_text() == "/nix/store/new-herdr\n"


def test_failed_handoff_preserves_active_identity(monkeypatch, tmp_path):
    active_package_file = _set_environment(monkeypatch, tmp_path)
    active_package_file.write_text("/nix/store/old-herdr\n")
    results = iter([_result(payload=_running_server()), _result(payload=_client())])

    def run_command(*arguments, **options):
        if arguments[1:3] == ("server", "live-handoff"):
            raise subprocess.CalledProcessError(1, arguments)
        return next(results)

    monkeypatch.setattr(reconcile_herdr_server, "run_command", run_command)
    with pytest.raises(subprocess.CalledProcessError):
        reconcile_herdr_server.main(["reconcile"])

    assert active_package_file.read_text() == "/nix/store/old-herdr\n"


def test_post_handoff_protocol_mismatch_preserves_identity(monkeypatch, tmp_path):
    active_package_file = _set_environment(monkeypatch, tmp_path)
    active_package_file.write_text("/nix/store/old-herdr\n")
    results = iter(
        [
            _result(payload=_running_server()),
            _result(payload=_client()),
            _result(),
            _result(payload=_running_server(protocol=15)),
        ]
    )
    monkeypatch.setattr(
        reconcile_herdr_server,
        "run_command",
        lambda *arguments, **options: next(results),
    )

    with pytest.raises(RuntimeError, match="protocol"):
        reconcile_herdr_server.main(["reconcile"])

    assert active_package_file.read_text() == "/nix/store/old-herdr\n"


def test_server_without_live_handoff_preserves_identity(monkeypatch, tmp_path):
    active_package_file = _set_environment(monkeypatch, tmp_path)
    active_package_file.write_text("/nix/store/old-herdr\n")
    monkeypatch.setattr(
        reconcile_herdr_server,
        "run_command",
        lambda *arguments, **options: _result(
            payload=_running_server(live_handoff=False)
        ),
    )

    with pytest.raises(RuntimeError, match="live handoff"):
        reconcile_herdr_server.main(["reconcile"])

    assert active_package_file.read_text() == "/nix/store/old-herdr\n"


def test_record_active_writes_desired_package_identity(monkeypatch, tmp_path):
    active_package_file = _set_environment(monkeypatch, tmp_path)

    reconcile_herdr_server.main(["record-active"])

    assert active_package_file.read_text() == "/nix/store/new-herdr\n"
