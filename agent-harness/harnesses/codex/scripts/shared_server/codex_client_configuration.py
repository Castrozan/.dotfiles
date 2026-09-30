import copy
from dataclasses import dataclass
import os
from pathlib import Path
import tomllib

from codex_shell_environment import client_shell_policy
from codex_client_arguments import parse_launch_arguments


@dataclass(frozen=True)
class ThreadPreparation:
    configuration: dict
    reuse_loaded: bool = False
    working_directory: str | None = None


def merge_configuration(base, overlay):
    merged = copy.deepcopy(base)
    for name, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(name), dict):
            merged[name] = merge_configuration(merged[name], value)
        else:
            merged[name] = copy.deepcopy(value)
    return merged


def command_line_configuration(arguments):
    options = parse_launch_arguments(arguments)
    profile = options.profile
    overrides = {}
    for override in options.config:
        overrides = merge_configuration(overrides, parse_override(override))
    if profile is None:
        return overrides
    home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    profile_path = home / f"{profile}.config.toml"
    if Path(profile).name != profile:
        raise ValueError("Codex profiles must be names within CODEX_HOME")
    return merge_configuration(tomllib.loads(profile_path.read_text()), overrides)


def parse_override(value):
    key, separator, raw = value.partition("=")
    if not separator:
        raise ValueError("Configuration override must contain =")
    try:
        return tomllib.loads(value)
    except tomllib.TOMLDecodeError:
        import json

        return tomllib.loads(f"{key}={json.dumps(raw)}")


def thread_configuration(parameters, configuration, environment, resolved=None):
    parameters = copy.deepcopy(parameters)
    overlay = merge_configuration(configuration, parameters.get("config") or {})
    overlay.pop("developer_instructions", None)
    effective = merge_configuration(resolved or {}, overlay)
    overlay["shell_environment_policy"] = client_shell_policy(
        environment, effective.get("shell_environment_policy") or {}
    )
    for name, server in (effective.get("mcp_servers") or {}).items():
        if server.get("command"):
            inherited_names = {
                "HOME",
                "LOGNAME",
                "PATH",
                "SHELL",
                "USER",
                "__CF_USER_TEXT_ENCODING",
                "LANG",
                "LC_ALL",
                "TERM",
                "TMPDIR",
                "TZ",
            }
            inherited_names.update(
                value
                for value in (server.get("env_vars") or [])
                if isinstance(value, str)
            )
            variables = {
                name: environment[name]
                for name in inherited_names
                if name in environment
            }
            variables.update(server.get("env") or {})
            overlay.setdefault("mcp_servers", {}).setdefault(name, {})["env"] = (
                variables
            )
    parameters["config"] = overlay
    return parameters
