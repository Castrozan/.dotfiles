import json
import os
import re
import sys
from pathlib import Path


def write_opencode_mcp(output: Path, name: str) -> None:
    configuration_path = output / ".opencode/opencode.jsonc"
    if not configuration_path.exists():
        return
    configuration = json.loads(configuration_path.read_text())
    for server_name, server in configuration.get("mcp", {}).items():
        if server.get("type") != "local":
            continue
        server["command"] = [
            sys.executable,
            str(Path(__file__).resolve()),
            server_name.removeprefix(f"plugin.{name}."),
        ]
    configuration_path.write_text(json.dumps(configuration, indent=2) + "\n")


def launch_server(server_name: str) -> None:
    plugin = Path(os.environ["PLUGIN_ROOT"]).resolve(strict=True)
    server = json.loads((plugin / "mcp.json").read_text())["mcpServers"][server_name]
    if server["type"] != "stdio":
        raise ValueError("Only declared stdio MCP servers can use this launcher")
    state = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    data = state / "agent-plugins/opencode" / plugin.name
    data.mkdir(parents=True, exist_ok=True)
    variables = {"PLUGIN_ROOT": str(plugin), "PLUGIN_DATA": str(data)}

    def expand(value):
        return re.sub(
            r"\$\{(PLUGIN_ROOT|PLUGIN_DATA)\}", lambda match: variables[match[1]], value
        )

    environment = (
        os.environ
        | {key: expand(value) for key, value in server.get("env", {}).items()}
        | variables
    )
    command = server["command"]
    if command.startswith("./"):
        command = str(plugin / command)
    arguments = [command, *map(expand, server.get("args", []))]
    directory = expand(server.get("cwd", "${PLUGIN_ROOT}"))
    os.chdir(plugin / directory if directory.startswith("./") else directory)
    os.execvpe(command, arguments, environment)


if __name__ == "__main__":
    launch_server(sys.argv[1])
