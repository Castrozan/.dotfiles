import dataclasses
import fcntl
import json
import os
import pathlib
import subprocess
import sys
import tempfile


@dataclasses.dataclass(frozen=True)
class ServerDeployment:
    executable: str
    package_identity: str
    active_package_file: pathlib.Path

    @classmethod
    def from_environment(cls):
        return cls(
            executable=os.environ["HERDR_EXECUTABLE"],
            package_identity=os.environ["HERDR_PACKAGE_IDENTITY"],
            active_package_file=pathlib.Path(os.environ["HERDR_ACTIVE_PACKAGE_FILE"]),
        )


def run_command(*arguments, check=False, timeout=15):
    return subprocess.run(
        arguments,
        check=check,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def read_active_package(active_package_file):
    try:
        return active_package_file.read_text().strip()
    except FileNotFoundError:
        return None


def write_active_package(deployment):
    parent_directory = deployment.active_package_file.parent
    parent_directory.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=parent_directory)
    temporary_path = pathlib.Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w") as temporary_file:
            temporary_file.write(f"{deployment.package_identity}\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, deployment.active_package_file)
    finally:
        temporary_path.unlink(missing_ok=True)


def read_json_command(*arguments, check=False):
    result = run_command(*arguments, check=check)
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)


def read_server_status(deployment):
    return read_json_command(
        deployment.executable,
        "status",
        "server",
        "--json",
    )


def read_client_status(deployment):
    return read_json_command(
        deployment.executable,
        "status",
        "client",
        "--json",
        check=True,
    )


def verify_server_status(server_status, client_status):
    if not server_status or not server_status.get("running"):
        raise RuntimeError("herdr server is unavailable after live handoff")
    if server_status.get("version") != client_status.get("version"):
        raise RuntimeError("herdr server version differs after live handoff")
    if server_status.get("protocol") != client_status.get("protocol"):
        raise RuntimeError("herdr server protocol differs after live handoff")


def reconcile_server(deployment):
    if (
        read_active_package(deployment.active_package_file)
        == deployment.package_identity
    ):
        return
    server_status = read_server_status(deployment)
    if not server_status or not server_status.get("running"):
        return
    capabilities = server_status.get("capabilities", {})
    if not capabilities.get("live_handoff"):
        raise RuntimeError("running herdr server does not support live handoff")
    client_status = read_client_status(deployment)
    run_command(
        deployment.executable,
        "server",
        "live-handoff",
        "--import-exe",
        deployment.executable,
        "--expected-protocol",
        str(client_status["protocol"]),
        "--expected-version",
        client_status["version"],
        check=True,
        timeout=120,
    )
    verify_server_status(read_server_status(deployment), client_status)
    write_active_package(deployment)


def with_deployment_lock(deployment, operation):
    deployment.active_package_file.parent.mkdir(parents=True, exist_ok=True)
    lock_file_path = deployment.active_package_file.with_suffix(".lock")
    with lock_file_path.open("a") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        operation(deployment)


def main(arguments=None):
    selected_arguments = sys.argv[1:] if arguments is None else arguments
    if len(selected_arguments) != 1:
        raise RuntimeError("expected one operation")
    operation_name = selected_arguments[0]
    deployment = ServerDeployment.from_environment()
    if operation_name == "reconcile":
        with_deployment_lock(deployment, reconcile_server)
        return
    if operation_name == "record-active":
        with_deployment_lock(deployment, write_active_package)
        return
    raise RuntimeError(f"unsupported operation: {operation_name}")


if __name__ == "__main__":
    main()
