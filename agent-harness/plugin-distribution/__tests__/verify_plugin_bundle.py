import json
import os
import subprocess
import sys
from pathlib import Path


def read_json(path):
    return json.loads(path.read_text())


def verify_mcp(command, environment):
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
        arguments = [
            value.replace("${PLUGIN_ROOT}", str(plugin)) for value in server["args"]
        ]
        verify_mcp([server["command"], *arguments], server["env"])

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
    server = read_json(bundle / ".opencode/opencode.jsonc")["mcp"][
        "plugin.distribution-probe.distribution-probe"
    ]
    verify_mcp(server["command"], server["environment"])
    for removed in ("input", ".git", "agents.toml", "agents.lock"):
        assert not (bundle / removed).exists()
    print("Skills, references, catalogs and MCP calls verified for all three targets")


if __name__ == "__main__":
    verify_bundle(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
