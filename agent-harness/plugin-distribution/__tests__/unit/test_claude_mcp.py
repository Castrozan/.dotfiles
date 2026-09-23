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
