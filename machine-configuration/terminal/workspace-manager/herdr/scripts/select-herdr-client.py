import json
import os
import pathlib
import subprocess
import sys
from typing import NamedTuple

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


RUNNING_SERVER_RECORD_ENVIRONMENT_VARIABLE = "HERDR_RUNNING_SERVER_RECORD"


class ServerClientSelectionError(RuntimeError):
    pass


class RunningServer(NamedTuple):
    socket_path: pathlib.Path
    process_identifier: int
    executable: pathlib.Path


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


def read_running_server(installed_executable):
    socket_path = read_running_server_socket(installed_executable)
    if socket_path is None:
        return None
    process_identifier = read_socket_owner_process_id(socket_path)
    return RunningServer(
        socket_path, process_identifier, read_process_executable(process_identifier)
    )


def read_running_server_executable(installed_executable):
    running_server = read_running_server(installed_executable)
    if running_server is None:
        return None
    return running_server.executable


def record_running_server(record_path, running_server):
    record_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = record_path.with_name(f"{record_path.name}.{os.getpid()}")
    temporary_path.write_text(
        f"{running_server.socket_path}\n{running_server.process_identifier}\n"
    )
    os.replace(temporary_path, record_path)


def select_client_executable(installed_executable, arguments, record_path=None):
    installed_path = pathlib.Path(installed_executable)
    if not command_requires_running_server_client(arguments):
        return installed_path
    running_server = read_running_server(installed_executable)
    if running_server is None:
        return installed_path
    if record_path is not None:
        record_running_server(record_path, running_server)
    return running_server.executable


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
        record_path = os.environ.get(RUNNING_SERVER_RECORD_ENVIRONMENT_VARIABLE)
        selected = select_client_executable(
            installed_executable,
            selected_arguments[2:],
            pathlib.Path(record_path) if record_path else None,
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
