import json
import subprocess

import update_enabled_plugins
from update_enabled_plugins import main, read_enabled_plugin_keys


class CompletedProcessStub:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def write_nix_source(tmp_path, monkeypatch, enabled_plugins):
    nix_source_path = tmp_path / "settings.json.nix-source"
    nix_source_path.write_text(json.dumps({"enabledPlugins": enabled_plugins}))
    monkeypatch.setattr(
        update_enabled_plugins, "claude_settings_nix_source_path", nix_source_path
    )
    return nix_source_path


def record_plugin_commands(monkeypatch, results=None):
    recorded_commands = []

    def fake_run(command, **_):
        recorded_commands.append(command)
        key = tuple(command[2:])
        return (results or {}).get(key, CompletedProcessStub())

    monkeypatch.setattr(subprocess, "run", fake_run)
    return recorded_commands


def test_reads_only_enabled_plugins_sorted(tmp_path, monkeypatch):
    write_nix_source(
        tmp_path,
        monkeypatch,
        {"zeta@shop": True, "alpha@shop": True, "disabled@shop": False},
    )

    assert read_enabled_plugin_keys() == ["alpha@shop", "zeta@shop"]


def test_missing_nix_source_yields_no_plugins(tmp_path, monkeypatch):
    monkeypatch.setattr(
        update_enabled_plugins,
        "claude_settings_nix_source_path",
        tmp_path / "absent.json",
    )

    assert read_enabled_plugin_keys() == []


def test_malformed_nix_source_yields_no_plugins(tmp_path, monkeypatch):
    nix_source_path = tmp_path / "settings.json.nix-source"
    nix_source_path.write_text("{not json")
    monkeypatch.setattr(
        update_enabled_plugins, "claude_settings_nix_source_path", nix_source_path
    )

    assert read_enabled_plugin_keys() == []


def test_updates_every_enabled_plugin(tmp_path, monkeypatch):
    write_nix_source(
        tmp_path,
        monkeypatch,
        {"alpha@shop": True, "beta@shop": True, "gamma@fair": True},
    )
    recorded_commands = record_plugin_commands(monkeypatch)

    assert main() == 0
    assert recorded_commands == [
        ["claude", "plugin", "update", "alpha@shop"],
        ["claude", "plugin", "update", "beta@shop"],
        ["claude", "plugin", "update", "gamma@fair"],
    ]


def test_a_failing_update_warns_without_failing_the_activation(
    tmp_path, monkeypatch, capsys
):
    write_nix_source(tmp_path, monkeypatch, {"alpha@shop": True})
    record_plugin_commands(
        monkeypatch,
        {
            ("update", "alpha@shop"): CompletedProcessStub(
                returncode=1, stderr="network unreachable"
            )
        },
    )

    assert main() == 0
    assert "could not update plugin alpha@shop" in capsys.readouterr().err


def test_no_enabled_plugins_runs_no_commands(tmp_path, monkeypatch):
    write_nix_source(tmp_path, monkeypatch, {})
    recorded_commands = record_plugin_commands(monkeypatch)

    assert main() == 0
    assert recorded_commands == []
