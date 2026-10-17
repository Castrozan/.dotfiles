import json
import shlex
import sys
from pathlib import Path


def configured_hook_command(plugin_directory, runtime_command, command):
    interpreter, source = shlex.split(command)
    if interpreter != "node" or not source.startswith("${CLAUDE_PLUGIN_ROOT}/hooks/"):
        raise ValueError(f"Unexpected upstream hook command: {command}")
    hook_path = plugin_directory / source.removeprefix("${CLAUDE_PLUGIN_ROOT}/")
    if not hook_path.is_file():
        raise FileNotFoundError(hook_path)
    return shlex.join([runtime_command, str(hook_path)])


def configure_plugin(plugin_directory, runtime_command):
    manifest_path = plugin_directory / ".claude-plugin/plugin.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["mcpServers"] = {
        "context-mode": {
            "command": runtime_command,
            "args": [str(plugin_directory / "cli.bundle.mjs")],
        }
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    hooks_path = plugin_directory / "hooks/hooks.json"
    configuration = json.loads(hooks_path.read_text())
    for entries in configuration["hooks"].values():
        for entry in entries:
            for hook in entry["hooks"]:
                hook["command"] = configured_hook_command(
                    plugin_directory, runtime_command, hook["command"]
                )
    hooks_path.write_text(json.dumps(configuration, indent=2) + "\n")


if __name__ == "__main__":
    configure_plugin(Path(sys.argv[1]), sys.argv[2])
