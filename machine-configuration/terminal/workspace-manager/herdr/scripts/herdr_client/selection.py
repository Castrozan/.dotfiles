import os
import pathlib


def command_does_not_need_server_client(arguments, installed_client_commands):
    command = arguments[0]
    if command in installed_client_commands:
        return True
    if command == "api":
        return arguments[1:2] != ["snapshot"]
    if command == "server":
        return is_server_management_command(arguments)
    return False


def is_server_management_command(arguments):
    return len(arguments) == 1 or arguments[1] in {
        "--help",
        "-h",
        "help",
        "live-handoff",
    }


def socket_path_from_status(status, selection_error):
    if status.get("running") is not True:
        return None
    socket_path = status.get("socket")
    if not isinstance(socket_path, str) or not socket_path:
        raise selection_error(
            "cannot identify the running Herdr server because status omitted its socket"
        )
    return pathlib.Path(socket_path)


def first_executable_path(stdout):
    for line in stdout.splitlines():
        if line.startswith("n"):
            return pathlib.Path(line[1:])
    return None


def is_executable_file(executable):
    return (
        executable is not None
        and executable.is_absolute()
        and executable.is_file()
        and os.access(executable, os.X_OK)
    )
