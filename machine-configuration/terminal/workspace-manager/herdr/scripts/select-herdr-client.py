import json
import os
import pathlib
import subprocess
import sys

from herdr_client import selection


INSTALLED_CLIENT_COMMANDS = frozenset(
    {
        "channel",
        "completion",
        "config",
        "integration",
        "machine",
        "status",
        "update",
    }
)


class ServerClientSelectionError(RuntimeError):
    pass


def run_command(*arguments):
    return subprocess.run(arguments, capture_output=True, text=True)


def command_requires_running_server_client(arguments):
    if not arguments or arguments[0].startswith("-"):
        return False
    return not selection.command_does_not_need_server_client(
        arguments, INSTALLED_CLIENT_COMMANDS
    )


def read_running_server_socket(installed_executable):
    result = run_command(
        installed_executable,
        "status",
        "server",
        "--json",
    )
    if result.returncode != 0:
        raise ServerClientSelectionError(
            "cannot identify the running Herdr server because status failed"
        )
    try:
        status = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise ServerClientSelectionError(
            "cannot identify the running Herdr server because status was invalid"
        ) from error
    if not isinstance(status, dict):
        raise ServerClientSelectionError(
            "cannot identify the running Herdr server because status was invalid"
        )
    return selection.socket_path_from_status(status, ServerClientSelectionError)


def read_socket_owner_process_id(socket_path):
    result = run_command(
        "lsof", "-n", "-t", "-a", "-c", "herdr", "--", str(socket_path)
    )
    process_identifiers = {
        int(line) for line in result.stdout.splitlines() if line.strip().isdigit()
    }
    if result.returncode != 0 or len(process_identifiers) != 1:
        raise ServerClientSelectionError(
            f"cannot identify the process serving {socket_path}"
        )
    return process_identifiers.pop()


def read_process_executable(process_identifier):
    result = run_command(
        "lsof",
        "-n",
        "-a",
        "-p",
        str(process_identifier),
        "-d",
        "txt",
        "-Fn",
    )
    if result.returncode != 0:
        raise ServerClientSelectionError(
            f"cannot identify Herdr server process {process_identifier}"
        )
    executable = selection.first_executable_path(result.stdout)
    if not selection.is_executable_file(executable):
        raise ServerClientSelectionError(
            f"cannot identify Herdr server process {process_identifier} executable"
        )
    return executable


def read_running_server_executable(installed_executable):
    socket_path = read_running_server_socket(installed_executable)
    if socket_path is None:
        return None
    process_identifier = read_socket_owner_process_id(socket_path)
    return read_process_executable(process_identifier)


def select_client_executable(installed_executable, arguments):
    installed_path = pathlib.Path(installed_executable)
    if not command_requires_running_server_client(arguments):
        return installed_path
    running_executable = read_running_server_executable(installed_executable)
    return running_executable or installed_path


def default_retention_root_path():
    state_home = os.environ.get("XDG_STATE_HOME")
    if state_home:
        return pathlib.Path(state_home) / "herdr" / "running-server-package"
    return pathlib.Path.home() / ".local" / "state" / "herdr" / "running-server-package"


def retain_executable_package(executable, root_path):
    executable_path = pathlib.Path(executable)
    if executable_path.name != "herdr" or executable_path.parent.name != "bin":
        raise ServerClientSelectionError(
            f"cannot identify Herdr package containing {executable_path}"
        )
    package_identity = executable_path.parents[1]
    root_path.parent.mkdir(parents=True, exist_ok=True)
    result = run_command(
        "nix-store",
        "--realise",
        str(package_identity),
        "--add-root",
        str(root_path),
        "--indirect",
    )
    if result.returncode != 0:
        raise ServerClientSelectionError(
            f"cannot retain running Herdr package {package_identity}"
        )


def main(arguments=None):
    selected_arguments = sys.argv[1:] if arguments is None else arguments
    if len(selected_arguments) < 2:
        raise ServerClientSelectionError(
            "expected an operation and installed executable"
        )
    operation = selected_arguments[0]
    installed_executable = selected_arguments[1]
    if operation == "select":
        selected = select_client_executable(
            installed_executable, selected_arguments[2:]
        )
        print(selected)
        return
    root_path = default_retention_root_path()
    _handle_retention_operation(operation, installed_executable, root_path)


def _handle_retention_operation(operation, installed_executable, root_path):
    if operation == "retain-installed":
        retain_executable_package(pathlib.Path(installed_executable), root_path)
        return
    if operation == "retain-running":
        running_executable = read_running_server_executable(installed_executable)
        if running_executable is not None:
            retain_executable_package(running_executable, root_path)
        return
    raise ServerClientSelectionError(f"unsupported operation: {operation}")


if __name__ == "__main__":
    try:
        main()
    except ServerClientSelectionError as error:
        print(f"herdr: {error}", file=sys.stderr)
        raise SystemExit(1) from error
