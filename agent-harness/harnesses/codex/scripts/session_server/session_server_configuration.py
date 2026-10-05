import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import tomllib

import tomlkit


@dataclass(frozen=True)
class CodexServerConfiguration:
    arguments: tuple[str, ...]
    working_directory: Path
    profile_path: Path | None


def toml_configuration_value(value):
    if isinstance(value, dict):
        table = tomlkit.inline_table()
        for key, entry in value.items():
            table.append(key, toml_configuration_value(entry))
        return table
    if isinstance(value, list):
        array = tomlkit.array()
        for entry in value:
            array.append(toml_configuration_value(entry))
        return array
    return tomlkit.item(value)


def profile_path_for(profile: str | None) -> Path | None:
    if profile is None:
        return None
    if Path(profile).name != profile or profile in {".", ".."}:
        raise ValueError("Codex profile must be a name")
    codex_directory = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    return (codex_directory / f"{profile}.config.toml").resolve()


def profile_configuration_arguments(profile_path: Path | None) -> list[str]:
    if profile_path is None:
        return []
    configuration = tomllib.loads(profile_path.read_text())
    arguments = []
    for key, value in configuration.items():
        arguments.extend(
            (
                "-c",
                f"{tomlkit.key(key).as_string()}={toml_configuration_value(value).as_string()}",
            )
        )
    return arguments


def server_configuration_for(arguments: list[str]) -> CodexServerConfiguration:
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument("-p", "--profile")
    parser.add_argument("-C", "--cd")
    parser.add_argument("-c", "--config", action="append", default=[])
    parser.add_argument("--enable", action="append", default=[])
    parser.add_argument("--disable", action="append", default=[])
    parser.add_argument("--strict-config", action="store_true")
    options, _ = parser.parse_known_args(arguments)
    profile_path = profile_path_for(options.profile)
    server_arguments = profile_configuration_arguments(profile_path)
    for override in options.config:
        server_arguments.extend(("-c", override))
    for feature in options.enable:
        server_arguments.extend(("--enable", feature))
    for feature in options.disable:
        server_arguments.extend(("--disable", feature))
    if options.strict_config:
        server_arguments.append("--strict-config")
    working_directory = Path(options.cd or Path.cwd()).expanduser().resolve()
    return CodexServerConfiguration(
        tuple(server_arguments), working_directory, profile_path
    )
