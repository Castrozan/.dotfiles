import json
import os
import sys
from pathlib import Path


def write_opencode_mcp(output: Path, name: str) -> None:
    configuration_path = output / ".opencode/opencode.jsonc"
    if not configuration_path.exists():
        return
    configuration = json.loads(configuration_path.read_text())
    for server in configuration.get("mcp", {}).values():
        if server.get("type") != "local":
            continue
        data = server["environment"]["PLUGIN_DATA"]
        server["command"] = [
            sys.executable,
            str(Path(__file__).resolve()),
            data,
            name,
            *server["command"],
        ]
    configuration_path.write_text(json.dumps(configuration, indent=2) + "\n")


def launch_server(previous_data: str, name: str, command: list[str]) -> None:
    state = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    data = state / "agent-plugins/opencode" / name
    data.mkdir(parents=True, exist_ok=True)
    environment = {
        key: value.replace(previous_data, str(data))
        for key, value in os.environ.items()
    }
    arguments = [value.replace(previous_data, str(data)) for value in command]
    os.chdir(str(Path.cwd()).replace(previous_data, str(data)))
    os.execvpe(arguments[0], arguments, environment)


if __name__ == "__main__":
    launch_server(sys.argv[1], sys.argv[2], sys.argv[3:])
