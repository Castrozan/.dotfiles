import json
import pathlib
import subprocess
import sys


def read_enabled_plugin_keys(settings_paths: list[pathlib.Path]) -> list[str]:
    enabled_plugin_keys: set[str] = set()
    for settings_path in settings_paths:
        if not settings_path.exists():
            continue
        try:
            settings = json.loads(settings_path.read_text())
        except json.JSONDecodeError:
            continue
        enabled_plugins = settings.get("enabledPlugins", {})
        if not isinstance(enabled_plugins, dict):
            continue
        enabled_plugin_keys.update(
            plugin_key
            for plugin_key, enabled in enabled_plugins.items()
            if enabled is True
        )
    return sorted(enabled_plugin_keys)


def run_claude_plugin_command(arguments: list[str]) -> tuple[bool, str]:
    completed_process = subprocess.run(
        ["claude", "plugin", *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    combined_output = (completed_process.stdout + completed_process.stderr).strip()
    return completed_process.returncode == 0, combined_output


def update_plugins(enabled_plugin_keys: list[str]) -> None:
    for plugin_key in enabled_plugin_keys:
        succeeded, output = run_claude_plugin_command(["update", plugin_key])
        if not succeeded:
            print(
                f"warning: could not update plugin {plugin_key}: {output}",
                file=sys.stderr,
            )
        elif "updated from" in output:
            print(output)


def main() -> int:
    settings_paths = [pathlib.Path(argument) for argument in sys.argv[1:]]
    enabled_plugin_keys = read_enabled_plugin_keys(settings_paths)
    if not enabled_plugin_keys:
        return 0
    update_plugins(enabled_plugin_keys)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
