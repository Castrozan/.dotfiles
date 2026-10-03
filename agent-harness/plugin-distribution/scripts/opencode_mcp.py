import json
from pathlib import Path


def _add_skill_path(configuration, plugin):
    skills = plugin / "skills"
    if skills.is_dir():
        paths = configuration.setdefault("skills", {}).setdefault("paths", [])
        if str(skills) not in paths:
            paths.append(str(skills))


def _rewrite_local_server(server, generated_data, data, plugin):
    if server.get("type") != "local":
        return
    server["command"] = [
        argument.replace(generated_data, str(data)) for argument in server["command"]
    ]
    if "cwd" in server:
        server["cwd"] = server["cwd"].replace(generated_data, str(data))
    server["environment"] = {
        key: value.replace(generated_data, str(data))
        for key, value in server.get("environment", {}).items()
    } | {"PLUGIN_ROOT": str(plugin), "PLUGIN_DATA": str(data)}


def write_opencode_configuration(output: Path, name: str, data_root: Path) -> None:
    data = data_root / name
    if not data_root.is_absolute() or data.resolve().is_relative_to(output.resolve()):
        raise ValueError("OpenCode plugin data must be absolute and outside the bundle")
    plugin = output / ".agents/plugins" / name
    generated_data = str(output / ".agents/plugin-data" / name)
    configuration_path = output / ".opencode/opencode.jsonc"
    configuration = (
        json.loads(configuration_path.read_text())
        if configuration_path.exists()
        else {}
    )
    configuration["$schema"] = "https://opencode.ai/config.json"
    _add_skill_path(configuration, plugin)
    for server in configuration.get("mcp", {}).values():
        _rewrite_local_server(server, generated_data, data, plugin)
    configuration_path.parent.mkdir(parents=True, exist_ok=True)
    configuration_path.write_text(
        json.dumps(configuration, indent=2)
        .replace("{env:", "\\u007benv:")
        .replace("{file:", "\\u007bfile:")
        + "\n"
    )
