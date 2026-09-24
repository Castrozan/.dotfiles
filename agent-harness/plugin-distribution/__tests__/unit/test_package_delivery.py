import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from build_plugin import build_plugin, deliver_package
from opencode_mcp import write_opencode_configuration


FIXTURE = Path(__file__).parents[1] / "fixtures/portable-plugin"


@pytest.mark.parametrize("targets", [(), ("pi", "hermes")])
def test_complete_package_needs_no_renderer(tmp_path, monkeypatch, targets):
    monkeypatch.delenv("DOTAGENTS_PLUGIN_BUILDER", raising=False)
    source = Path(shutil.copytree(FIXTURE, tmp_path / "source"))
    (source / "arbitrary-artifact.bin").write_bytes(bytes(range(256)))
    output = tmp_path / "output"
    build_plugin(source, output, targets)
    for path in source.rglob("*"):
        if path.is_file():
            assert (
                output / "plugin" / path.relative_to(source)
            ).read_bytes() == path.read_bytes()
    assert not (output / ".agents/skills").exists()


def test_authored_manifests_survive_renderer_changes(tmp_path):
    source = tmp_path / "source"
    native = source / ".claude-plugin"
    native.mkdir(parents=True)
    authored = '{"name":"example","hooks":"./custom-hooks.json"}'
    (native / "plugin.json").write_text(authored)
    output = tmp_path / "output"
    generated = output / ".agents/plugins/example/.claude-plugin"
    generated.mkdir(parents=True)
    (generated / "plugin.json").write_text('{"name":"example"}')
    deliver_package(source, output, "example", ())
    assert (generated / "plugin.json").read_text() == authored


def test_renderer_file_links_are_materialized_on_source_restoration(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "asset").write_bytes(b"opaque")
    (source / "link").symlink_to("asset")
    output = tmp_path / "output"
    generated = output / ".agents/plugins/example"
    generated.mkdir(parents=True)
    (generated / "asset").write_bytes(b"opaque")
    (generated / "link").symlink_to("asset")
    deliver_package(source, output, "example", ())
    assert not (generated / "link").is_symlink()
    assert (generated / "link").read_bytes() == b"opaque"


def test_opencode_data_survives_bundle_updates_outside_package(tmp_path):
    state = tmp_path / "state"
    for revision in ("first", "second"):
        output = tmp_path / revision
        data = output / ".agents/plugin-data/example"
        data.mkdir(parents=True)
        plugin = output / ".agents/plugins/example"
        plugin.mkdir(parents=True)
        configuration = output / ".opencode/opencode.jsonc"
        configuration.parent.mkdir()
        server = {
            "type": "local",
            "command": [
                sys.executable,
                "-c",
                'import os,pathlib,sys; p=pathlib.Path(os.environ["PLUGIN_DATA"])/"state"; '
                'p.write_text((p.read_text() if p.exists() else "")+sys.argv[1]); print(p)',
                revision,
            ],
            "environment": {"PLUGIN_DATA": str(data)},
            "cwd": str(data),
        }
        server["environment"]["PLUGIN_ROOT"] = str(plugin)
        (plugin / "mcp.json").write_text(
            json.dumps(
                {
                    "mcpServers": {
                        "example": {
                            "type": "stdio",
                            "command": server["command"][0],
                            "args": server["command"][1:],
                            "cwd": "${PLUGIN_DATA}",
                        }
                    }
                }
            )
        )
        configuration.write_text(
            json.dumps({"mcp": {"plugin.example.example": server}})
        )
        write_opencode_configuration(output, "example")
        emitted = json.loads(configuration.read_text())["mcp"]["plugin.example.example"]
        result = subprocess.run(
            emitted["command"],
            cwd=emitted["cwd"],
            env=os.environ | emitted["environment"] | {"XDG_STATE_HOME": str(state)},
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        assert Path(result.stdout.strip()).is_relative_to(state)
        assert not (data / "state").exists()
    assert (state / "agent-plugins/opencode/example/state").read_text() == "firstsecond"


def test_opencode_adapter_leaves_remote_server_unchanged(tmp_path):
    path = tmp_path / ".opencode/opencode.jsonc"
    path.parent.mkdir()
    server = {"type": "remote", "url": "https://example.com/mcp"}
    path.write_text(json.dumps({"mcp": {"remote": server}}))
    write_opencode_configuration(tmp_path, "example")
    assert json.loads(path.read_text())["mcp"]["remote"] == server


def test_opencode_skill_only_package_has_immutable_discovery_configuration(tmp_path):
    skills = tmp_path / ".agents/plugins/example/skills"
    skills.mkdir(parents=True)
    write_opencode_configuration(tmp_path, "example")
    path = tmp_path / ".opencode/opencode.jsonc"
    configuration = json.loads(path.read_text())
    assert configuration["$schema"] == "https://opencode.ai/config.json"
    assert configuration["skills"]["paths"] == [str(skills)]


def test_opencode_launcher_expands_data_in_arguments_and_environment(
    tmp_path, monkeypatch
):
    from opencode_mcp import launch_server

    plugin = tmp_path / "example"
    plugin.mkdir()
    (plugin / "mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "declared": {
                        "type": "stdio",
                        "command": "./server",
                        "args": ["${PLUGIN_DATA}/config.json"],
                        "env": {
                            "CONFIG": "${PLUGIN_ROOT}/config",
                            "LITERAL": "${HOME}",
                        },
                        "cwd": "${PLUGIN_DATA}",
                    }
                }
            }
        )
    )
    monkeypatch.chdir(plugin)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("PLUGIN_ROOT", str(plugin))
    captured = []
    monkeypatch.setattr(os, "execvpe", lambda *arguments: captured.append(arguments))
    launch_server("declared")
    expected = tmp_path / "state/agent-plugins/opencode/example"
    command, arguments, environment = captured[0]
    assert command == str(plugin / "server")
    assert arguments == [str(plugin / "server"), str(expected / "config.json")]
    assert environment["PLUGIN_DATA"] == str(expected)
    assert environment["CONFIG"] == str(plugin / "config")
    assert environment["LITERAL"] == "${HOME}"
    assert Path.cwd() == expected


@pytest.mark.parametrize("server_name", ["unknown-command", "remote"])
def test_opencode_launcher_cannot_accept_an_arbitrary_command(
    tmp_path, monkeypatch, server_name
):
    from opencode_mcp import launch_server

    (tmp_path / "mcp.json").write_text(
        '{"mcpServers":{"remote":{"type":"sse","url":"https://example.com/mcp"}}}'
    )
    monkeypatch.setenv("PLUGIN_ROOT", str(tmp_path))
    with pytest.raises((KeyError, ValueError)):
        launch_server(server_name)
