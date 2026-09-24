import json
from pathlib import Path


CLAUDE_PLUGIN_ROOT_VARIABLE = "${CLAUDE_PLUGIN_ROOT}"


def write_claude_mcp(plugin: Path, shell: str) -> None:
    source = plugin / "mcp.json"
    if not source.is_file():
        return
    configuration = json.loads(
        source.read_text()
        .replace("${PLUGIN_ROOT}", CLAUDE_PLUGIN_ROOT_VARIABLE)
        .replace("${PLUGIN_DATA}", "${CLAUDE_PLUGIN_DATA}")
    )
    for server in configuration["mcpServers"].values():
        if server.get("type", "stdio") != "stdio":
            continue
        directory = server.pop("cwd", CLAUDE_PLUGIN_ROOT_VARIABLE)
        if not directory.startswith("${CLAUDE_PLUGIN_"):
            directory = CLAUDE_PLUGIN_ROOT_VARIABLE + "/" + directory
        server["args"] = [
            "-c",
            'cd -- "$1" && shift && exec "$@"',
            "agent-plugin-mcp",
            directory,
            server["command"],
            *server.get("args", []),
        ]
        server["command"] = shell
        server["env"] = server.get("env", {}) | {
            "PLUGIN_ROOT": CLAUDE_PLUGIN_ROOT_VARIABLE,
            "PLUGIN_DATA": "${CLAUDE_PLUGIN_DATA}",
        }
    destination = plugin / ".claude-plugin"
    (destination / "mcp.json").write_text(json.dumps(configuration, indent=2) + "\n")
    manifest_path = destination / "plugin.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["mcpServers"] = "./.claude-plugin/mcp.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
