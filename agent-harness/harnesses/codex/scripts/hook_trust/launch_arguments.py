import argparse
from dataclasses import dataclass
from pathlib import Path


configuration_commands = frozenset(
    {
        "login",
        "logout",
        "mcp",
        "plugin",
        "mcp-server",
        "app-server",
        "remote-control",
        "app",
        "completion",
        "update",
        "doctor",
        "sandbox",
        "debug",
        "apply",
        "a",
        "queue",
        "archive",
        "delete",
        "migrate-rollouts",
        "unarchive",
        "cloud",
        "exec-server",
        "features",
        "help",
    }
)


@dataclass(frozen=True)
class HookDiscoveryRequest:
    working_directory: Path
    configuration_arguments: tuple[str, ...]
    include_session_directories: bool


def discover_launch_request(arguments: list[str]) -> HookDiscoveryRequest | None:
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument("-C", "--cd")
    parser.add_argument("-c", "--config", action="append", default=[])
    parser.add_argument("--enable", action="append", default=[])
    parser.add_argument("--disable", action="append", default=[])
    parser.add_argument("-p", "--profile")
    parser.add_argument("-m", "--model")
    parser.add_argument("-i", "--image", action="append")
    parser.add_argument("-s", "--sandbox")
    parser.add_argument("-a", "--ask-for-approval")
    parser.add_argument("--add-dir", action="append")
    parser.add_argument("--local-provider")
    parser.add_argument("--remote")
    parser.add_argument("--remote-auth-token-env")
    parser.add_argument("-h", "--help", "-V", "--version", action="store_true")
    options, remaining = parser.parse_known_args(arguments)
    command = _first_positional_argument(remaining)
    if _is_configuration_launch(options, command):
        return None
    configuration_arguments = _configuration_arguments(options)
    working_directory = Path(options.cd or Path.cwd()).expanduser().resolve()
    return HookDiscoveryRequest(
        working_directory,
        tuple(configuration_arguments),
        _includes_session_directories(command, options.cd),
    )


def _first_positional_argument(remaining: list[str]) -> str | None:
    return next(
        (argument for argument in remaining if not argument.startswith("-")), None
    )


def _is_configuration_launch(options, command: str | None) -> bool:
    return options.help or options.remote or command in configuration_commands


def _configuration_arguments(options) -> list[str]:
    configuration_arguments = [
        argument for override in options.config for argument in ("-c", override)
    ]
    for feature in options.enable:
        configuration_arguments.extend(("--enable", feature))
    for feature in options.disable:
        configuration_arguments.extend(("--disable", feature))
    return configuration_arguments


def _includes_session_directories(
    command: str | None, change_directory: str | None
) -> bool:
    return command in {"resume", "fork", "agents"} and change_directory is None
