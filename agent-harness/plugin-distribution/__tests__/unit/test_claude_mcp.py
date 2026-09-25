import json
import os
import shutil
import subprocess

import pytest

from claude_mcp import write_claude_mcp


@pytest.mark.parametrize("directory", [None, "working directory"])
def test_stdio_keeps_runtime_paths_and_literal_arguments(tmp_path, directory):
    plugin = tmp_path / "plugin with spaces"
    native = plugin / ".claude-plugin"
    native.mkdir(parents=True)
    (native / "plugin.json").write_text('{"name":"example","skills":"./skills"}')
    server = {
        "type": "stdio",
        "command": "sh",
        "args": [
            "-c",
            'printf "%s\\n" "$PWD" "$PLUGIN_ROOT" "$1"',
            "probe",
            "$(exit 99)",
        ],
        "env": {"DATA_PATH": "${PLUGIN_DATA}/state"},
    }
    if directory is not None:
        (plugin / directory).mkdir()
        server["cwd"] = directory
    source = json.dumps({"mcpServers": {"example": server}})
    (plugin / "mcp.json").write_text(source)
    write_claude_mcp(plugin, shutil.which("bash"))
    assert (plugin / "mcp.json").read_text() == source
    manifest = json.loads((native / "plugin.json").read_text())
    assert manifest["skills"] == "./skills"
    configuration = (plugin / manifest["mcpServers"]).read_text()
    configuration = configuration.replace(
        "${CLAUDE_PLUGIN_ROOT}", str(plugin.resolve())
    )
    configuration = configuration.replace("${CLAUDE_PLUGIN_DATA}", str(tmp_path))
    emitted = json.loads(configuration)["mcpServers"]["example"]
    process = subprocess.run(
        [emitted["command"], *emitted["args"]],
        cwd=tmp_path,
        env=os.environ | emitted["env"],
        capture_output=True,
        text=True,
        check=True,
        timeout=5,
    )
    assert process.stdout.splitlines() == [
        str((plugin / (directory or "")).resolve()),
        str(plugin.resolve()),
        "$(exit 99)",
    ]
    assert emitted["env"]["DATA_PATH"] == str(tmp_path) + "/state"


def test_http_has_no_process_launcher(tmp_path):
    native = tmp_path / ".claude-plugin"
    native.mkdir()
    (native / "plugin.json").write_text('{"name":"example"}')
    server = {"type": "http", "url": "https://example.com/mcp"}
    (tmp_path / "mcp.json").write_text(json.dumps({"mcpServers": {"example": server}}))
    write_claude_mcp(tmp_path, "unused-shell")
    assert (
        json.loads((native / "mcp.json").read_text())["mcpServers"]["example"] == server
    )


def test_skill_only_plugin_needs_no_mcp_adapter(tmp_path):
    write_claude_mcp(tmp_path, "unused-shell")
    assert list(tmp_path.iterdir()) == []


def test_authored_mcp_file_is_not_overwritten(tmp_path):
    native = tmp_path / ".claude-plugin"
    native.mkdir()
    (native / "plugin.json").write_text('{"name":"example"}')
    authored = '{"mcpServers":{"native":{"command":"native-server"}}}'
    (native / "mcp.json").write_text(authored)
    (tmp_path / "mcp.json").write_text('{"mcpServers":{}}')
    write_claude_mcp(tmp_path, "unused-shell")
    assert (native / "mcp.json").read_text() == authored
    manifest = json.loads((native / "plugin.json").read_text())
    assert manifest["mcpServers"] == "./.claude-plugin/mcp.generated.1.json"


@pytest.mark.parametrize("working_directory", ["./working directory", "${PLUGIN_DATA}"])
@pytest.mark.parametrize("shadow_command", [False, True])
def test_relative_command_keeps_package_origin_after_changing_directory(
    tmp_path, working_directory, shadow_command
):
    plugin = tmp_path / "package with spaces"
    native = plugin / ".claude-plugin"
    native.mkdir(parents=True)
    (native / "plugin.json").write_text('{"name":"example"}')
    executable = plugin / "bin/server"
    executable.parent.mkdir()
    executable.write_text('#!/bin/sh\nprintf "canonical\\n%s\\n%s\\n" "$PWD" "$1"\n')
    executable.chmod(0o755)
    data = tmp_path / "persistent data"
    directory = (
        data if working_directory == "${PLUGIN_DATA}" else plugin / working_directory
    )
    directory.mkdir()
    if shadow_command:
        shadow = directory / "bin/server"
        shadow.parent.mkdir()
        shadow.write_text('#!/bin/sh\nprintf "wrong-origin\\n"\n')
        shadow.chmod(0o755)
    portable = {
        "mcpServers": {
            "example": {
                "type": "stdio",
                "command": "./bin/server",
                "args": ["$(exit 99)"],
                "cwd": working_directory,
            }
        }
    }
    source = json.dumps(portable)
    (plugin / "mcp.json").write_text(source)
    write_claude_mcp(plugin, shutil.which("bash"))
    emitted = json.loads(
        (native / "mcp.json")
        .read_text()
        .replace("${CLAUDE_PLUGIN_ROOT}", str(plugin))
        .replace("${CLAUDE_PLUGIN_DATA}", str(data))
    )["mcpServers"]["example"]
    result = subprocess.run(
        [emitted["command"], *emitted["args"]],
        cwd=tmp_path,
        env=os.environ | emitted["env"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["canonical", str(directory), "$(exit 99)"]
    assert (plugin / "mcp.json").read_text() == source
