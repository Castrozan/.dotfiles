import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from build_plugin import build_plugin, deliver_package
from opencode_mcp import write_opencode_mcp


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


def test_opencode_data_survives_bundle_updates_outside_package(tmp_path):
    state = tmp_path / "state"
    for revision in ("first", "second"):
        output = tmp_path / revision
        data = output / ".agents/plugin-data/example"
        data.mkdir(parents=True)
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
        configuration.write_text(json.dumps({"mcp": {"example": server}}))
        write_opencode_mcp(output, "example")
        emitted = json.loads(configuration.read_text())["mcp"]["example"]
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
        assert list(data.iterdir()) == []
    assert (state / "agent-plugins/opencode/example/state").read_text() == "firstsecond"


def test_opencode_adapter_leaves_remote_server_unchanged(tmp_path):
    write_opencode_mcp(tmp_path, "example")
    path = tmp_path / ".opencode/opencode.jsonc"
    path.parent.mkdir()
    server = {"type": "remote", "url": "https://example.com/mcp"}
    path.write_text(json.dumps({"mcp": {"remote": server}}))
    write_opencode_mcp(tmp_path, "example")
    assert json.loads(path.read_text())["mcp"]["remote"] == server


def test_opencode_launcher_expands_data_in_arguments_and_environment(
    tmp_path, monkeypatch
):
    from opencode_mcp import launch_server

    previous = tmp_path / "immutable-data"
    previous.mkdir()
    monkeypatch.chdir(previous)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("PLUGIN_DATA", str(previous))
    captured = []
    monkeypatch.setattr(os, "execvpe", lambda *arguments: captured.append(arguments))
    launch_server(str(previous), "example", ["server", str(previous / "config.json")])
    expected = tmp_path / "state/agent-plugins/opencode/example"
    command, arguments, environment = captured[0]
    assert command == "server"
    assert arguments == ["server", str(expected / "config.json")]
    assert environment["PLUGIN_DATA"] == str(expected)
    assert Path.cwd() == expected
