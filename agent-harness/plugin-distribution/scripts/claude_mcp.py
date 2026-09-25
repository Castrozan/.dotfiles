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
        command = server["command"]
        if command.startswith("./"):
            command = CLAUDE_PLUGIN_ROOT_VARIABLE + command[1:]
        server["args"] = [
            "-c",
            'cd -- "$1" && shift && exec "$@"',
            "agent-plugin-mcp",
            directory,
            command,
            *server.get("args", []),
        ]
        server["command"] = shell
        server["env"] = server.get("env", {}) | {
            "PLUGIN_ROOT": CLAUDE_PLUGIN_ROOT_VARIABLE,
            "PLUGIN_DATA": "${CLAUDE_PLUGIN_DATA}",
        }
    destination = plugin / ".claude-plugin"
    adapter = destination / "mcp.json"
    sequence = 0
    while adapter.exists():
        sequence += 1
        adapter = destination / f"mcp.generated.{sequence}.json"
    adapter.write_text(json.dumps(configuration, indent=2) + "\n")
    manifest_path = destination / "plugin.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["mcpServers"] = "./" + str(adapter.relative_to(plugin))
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
