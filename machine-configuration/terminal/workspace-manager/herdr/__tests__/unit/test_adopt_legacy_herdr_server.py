import importlib.util
import pathlib
import sys
from types import SimpleNamespace

SCRIPT_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "scripts"
    / "adopt-legacy-herdr-server.py"
)


def _load_module():
    module_spec = importlib.util.spec_from_file_location(
        "adopt_legacy_herdr_server", SCRIPT_PATH
    )
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    return module


adopt_legacy_herdr_server = _load_module()


def _set_environment(monkeypatch):
    monkeypatch.setenv("HERDR_LEGACY_UNIT", "legacy.service")
    monkeypatch.setenv("HERDR_TARGET_UNIT", "herdr.service")
    monkeypatch.setenv("HERDR_EXECUTABLE", "/nix/store/new/bin/herdr")
    monkeypatch.setenv("HERDR_IMPORT_EXECUTABLE", "/nix/store/import/bin/herdr")
    monkeypatch.setenv(
        "HERDR_RECONCILER", "/nix/store/reconcile/bin/reconcile-herdr-server"
    )


def test_successful_adoption_records_imported_package(monkeypatch):
    _set_environment(monkeypatch)
    commands = []
    signals = []
    monkeypatch.setattr(adopt_legacy_herdr_server, "unit_is_active", lambda unit: True)
    monkeypatch.setattr(
        adopt_legacy_herdr_server,
        "unit_property",
        lambda unit, property_name: "123",
    )
    monkeypatch.setattr(
        adopt_legacy_herdr_server.os,
        "kill",
        lambda process_id, sent_signal: signals.append((process_id, sent_signal)),
    )
    monkeypatch.setattr(
        adopt_legacy_herdr_server, "process_exists", lambda process_id: True
    )
    monkeypatch.setattr(
        adopt_legacy_herdr_server,
        "run_command",
        lambda *arguments, **options: commands.append((arguments, options))
        or SimpleNamespace(returncode=0, stdout="", stderr=""),
    )
    monkeypatch.setattr(
        adopt_legacy_herdr_server, "herdr_server_is_running", lambda: True
    )
    monkeypatch.setattr(
        adopt_legacy_herdr_server,
        "wait_for_legacy_unit_stop",
        lambda unit: True,
    )

    adopt_legacy_herdr_server.adopt_legacy_server()

    assert [arguments for arguments, _ in commands][-1] == (
        "/nix/store/reconcile/bin/reconcile-herdr-server",
        "record-active",
    )
    assert [sent_signal for _, sent_signal in signals] == [
        adopt_legacy_herdr_server.signal.SIGSTOP,
        adopt_legacy_herdr_server.signal.SIGCONT,
    ]


def test_absent_legacy_service_does_not_record_package(monkeypatch):
    _set_environment(monkeypatch)
    commands = []
    monkeypatch.setattr(adopt_legacy_herdr_server, "unit_is_active", lambda unit: False)
    monkeypatch.setattr(
        adopt_legacy_herdr_server,
        "run_command",
        lambda *arguments, **options: commands.append((arguments, options)),
    )

    adopt_legacy_herdr_server.adopt_legacy_server()

    assert commands == []
