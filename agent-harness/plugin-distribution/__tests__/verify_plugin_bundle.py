import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def read_json(path):
    return json.loads(path.read_text())


def verify_mcp(command, environment, directory=None):
    requests = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "distribution-check", "version": "1"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "distribution_echo",
                "arguments": {"token": "native-artifact"},
            },
        },
    ]
    process = subprocess.run(
        command,
        env=os.environ | environment,
        cwd=directory,
        input="".join(json.dumps(request) + "\n" for request in requests),
        capture_output=True,
        text=True,
        check=True,
        timeout=5,
    )
    responses = [json.loads(line) for line in process.stdout.splitlines()]
    assert responses[0]["result"]["serverInfo"]["name"] == "distribution-probe"
    assert responses[1]["result"]["tools"][0]["name"] == "distribution_echo"
    assert responses[2]["result"]["content"][0]["text"] == (
        "distributed:native-artifact"
    )


def verify_bundle(bundle, source):
    plugin = bundle / ".agents/plugins/distribution-probe"
    assert (bundle / "plugin").resolve() == plugin
    for path in source.rglob("*"):
        if path.is_file():
            assert (plugin / path.relative_to(source)).read_bytes() == path.read_bytes()
    for target in ("pi", "hermes"):
        assert (bundle / f".{target}/plugins/distribution-probe").resolve() == plugin
    for target in ("claude", "codex"):
        manifest = read_json(plugin / f".{target}-plugin/plugin.json")
        assert manifest["name"] == "distribution-probe"
        skill_directory = plugin / manifest["skills"] / "distribution-probe"
        for relative in ("SKILL.md", "references/expected.md"):
            assert (skill_directory / relative).read_bytes() == (
                source / "skills/distribution-probe" / relative
            ).read_bytes()
        server = read_json(plugin / manifest["mcpServers"])["mcpServers"][
            "distribution-probe"
        ]
        placeholder = (
            "${CLAUDE_PLUGIN_ROOT}" if target == "claude" else "${PLUGIN_ROOT}"
        )
        serialized = json.dumps(server).replace(placeholder, str(plugin))
        if target == "claude":
            assert "${PLUGIN_ROOT}" not in serialized
            serialized = serialized.replace("${CLAUDE_PLUGIN_DATA}", str(plugin))
        server = json.loads(serialized)
        environment = {"PLUGIN_ROOT": str(plugin)} | server["env"]
        verify_mcp(
            [server["command"], *server["args"]],
            environment,
            plugin if target == "codex" else None,
        )

    claude_marketplace = read_json(bundle / ".claude-plugin/marketplace.json")
    assert (bundle / claude_marketplace["plugins"][0]["source"]).resolve() == plugin
    codex_marketplace = read_json(bundle / ".agents/plugins/marketplace.json")
    assert (
        bundle / codex_marketplace["plugins"][0]["source"]["path"]
    ).resolve() == plugin
    opencode_skill = bundle / ".opencode/skills/distribution-probe"
    assert (opencode_skill / "references/expected.md").read_bytes() == (
        source / "skills/distribution-probe/references/expected.md"
    ).read_bytes()
    opencode = read_json(bundle / ".opencode/opencode.jsonc")
    assert opencode["$schema"] == "https://opencode.ai/config.json"
    assert opencode["skills"]["paths"] == [str(plugin / "skills")]
    server = opencode["mcp"]["plugin.distribution-probe.distribution-probe"]
    with tempfile.TemporaryDirectory() as state:
        verify_mcp(
            server["command"],
            server["environment"] | {"XDG_STATE_HOME": state},
            server["cwd"],
        )
    for removed in ("input", ".git", "agents.toml", "agents.lock"):
        assert not (bundle / removed).exists()
    print(
        "Complete packages for five targets and MCP calls through three native adapters verified"
    )


if __name__ == "__main__":
    verify_bundle(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
