import json
import subprocess
import sys

from update_enabled_plugins import main, read_enabled_plugin_keys


class CompletedProcessStub:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def write_settings(tmp_path, file_name, enabled_plugins):
    settings_path = tmp_path / file_name
    settings_path.write_text(json.dumps({"enabledPlugins": enabled_plugins}))
    return settings_path


def run_main_over(monkeypatch, settings_paths):
    monkeypatch.setattr(
        sys, "argv", ["update_enabled_plugins", *map(str, settings_paths)]
    )
    return main()


def record_plugin_commands(monkeypatch, results=None):
    recorded_commands = []

    def fake_run(command, **_):
        recorded_commands.append(command)
        key = tuple(command[2:])
        return (results or {}).get(key, CompletedProcessStub())

    monkeypatch.setattr(subprocess, "run", fake_run)
    return recorded_commands


def test_reads_only_enabled_plugins_sorted(tmp_path):
    nix_source_path = write_settings(
        tmp_path,
        "settings.json.nix-source",
        {"zeta@shop": True, "alpha@shop": True, "disabled@shop": False},
    )

    assert read_enabled_plugin_keys([nix_source_path]) == ["alpha@shop", "zeta@shop"]


def test_unions_enabled_plugins_across_every_settings_file(tmp_path):
    nix_source_path = write_settings(
        tmp_path, "settings.json.nix-source", {"alpha@shop": True}
    )
    workspace_profile_path = write_settings(
        tmp_path,
        "claude-workspace-profile-work-settings.json",
        {"alpha@shop": True, "beta@shop": True},
    )

    assert read_enabled_plugin_keys([nix_source_path, workspace_profile_path]) == [
        "alpha@shop",
        "beta@shop",
    ]


def test_missing_settings_file_yields_no_plugins(tmp_path):
    assert read_enabled_plugin_keys([tmp_path / "absent.json"]) == []


def test_malformed_settings_file_yields_no_plugins(tmp_path):
    malformed_path = tmp_path / "settings.json.nix-source"
    malformed_path.write_text("{not json")

    assert read_enabled_plugin_keys([malformed_path]) == []


def test_updates_every_enabled_plugin(tmp_path, monkeypatch):
    nix_source_path = write_settings(
        tmp_path,
        "settings.json.nix-source",
        {"alpha@shop": True, "beta@shop": True, "gamma@fair": True},
    )
    recorded_commands = record_plugin_commands(monkeypatch)

    assert run_main_over(monkeypatch, [nix_source_path]) == 0
    assert recorded_commands == [
        ["claude", "plugin", "update", "alpha@shop"],
        ["claude", "plugin", "update", "beta@shop"],
        ["claude", "plugin", "update", "gamma@fair"],
    ]


def test_updates_a_plugin_only_a_workspace_profile_enables(tmp_path, monkeypatch):
    nix_source_path = write_settings(tmp_path, "settings.json.nix-source", {})
    workspace_profile_path = write_settings(
        tmp_path, "claude-workspace-profile-work-settings.json", {"alpha@shop": True}
    )
    recorded_commands = record_plugin_commands(monkeypatch)

    assert run_main_over(monkeypatch, [nix_source_path, workspace_profile_path]) == 0
    assert recorded_commands == [["claude", "plugin", "update", "alpha@shop"]]


def test_a_failing_update_warns_without_failing_the_activation(
    tmp_path, monkeypatch, capsys
):
    nix_source_path = write_settings(
        tmp_path, "settings.json.nix-source", {"alpha@shop": True}
    )
    record_plugin_commands(
        monkeypatch,
        {
            ("update", "alpha@shop"): CompletedProcessStub(
                returncode=1, stderr="network unreachable"
            )
        },
    )

    assert run_main_over(monkeypatch, [nix_source_path]) == 0
    assert "could not update plugin alpha@shop" in capsys.readouterr().err


def test_no_enabled_plugins_runs_no_commands(tmp_path, monkeypatch):
    nix_source_path = write_settings(tmp_path, "settings.json.nix-source", {})
    recorded_commands = record_plugin_commands(monkeypatch)

    assert run_main_over(monkeypatch, [nix_source_path]) == 0
    assert recorded_commands == []


def test_no_settings_file_at_all_runs_no_commands(monkeypatch):
    recorded_commands = record_plugin_commands(monkeypatch)

    assert run_main_over(monkeypatch, []) == 0
    assert recorded_commands == []
