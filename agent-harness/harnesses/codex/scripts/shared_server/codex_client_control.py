import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

from codex_shell_environment import CORE_VARIABLES


def control_directory(home):
    identity = hashlib.sha256(str(home.resolve()).encode()).hexdigest()[:16]
    directory = Path(f"/tmp/codex-proxy-{os.getuid()}-{identity}")
    directory.mkdir(mode=0o700, exist_ok=True)
    status = directory.lstat()
    if directory.is_symlink() or status.st_uid != os.getuid() or status.st_mode & 0o077:
        raise RuntimeError(
            "Codex proxy directory must be private and owned by this user"
        )
    return directory


def request(socket_path, message):
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(90)
        connection.connect(str(socket_path))
        connection.sendall(json.dumps(message).encode() + b"\n")
        with connection.makefile("rb") as stream:
            result = json.loads(stream.readline(65536))
        if "error" in result:
            raise RuntimeError(result["error"])
        return result


def proxy_generation(binary):
    return [str(Path(__file__).resolve().parent), str(Path(binary).resolve())]


def register_client(environment, configuration) -> str | None:
    environment = {**environment, "PWD": os.getcwd()}
    home = Path(environment.get("CODEX_HOME", Path.home() / ".codex")).resolve()
    directory = control_directory(home)
    socket_path = directory / "control.sock"
    generation = proxy_generation(environment["CODEX_LAUNCHER_BINARY"])
    descriptor = os.open(directory / "startup.lock", os.O_CREAT | os.O_RDWR, 0o600)
    with os.fdopen(descriptor, "w") as startup:
        fcntl.flock(startup, fcntl.LOCK_EX)
        try:
            status = request(socket_path, {"method": "status"})
            if status["generation"] != generation:
                try:
                    request(socket_path, {"method": "shutdown"})
                except RuntimeError:
                    return None
                deadline = time.monotonic() + 5
                while socket_path.exists() and time.monotonic() < deadline:
                    time.sleep(0.05)
                if socket_path.exists():
                    raise RuntimeError("Previous Codex proxy is still shutting down")
                status = None
        except (FileNotFoundError, ConnectionRefusedError):
            status = None
        if status is None:
            start_host(home, environment, directory, socket_path)
        return request(
            socket_path,
            {
                "method": "register",
                "environment": environment,
                "configuration": configuration,
                "processId": os.getpid(),
            },
        )["endpoint"]


def start_host(home, environment, directory, socket_path):
    daemon_environment = {
        name: value for name, value in environment.items() if name in CORE_VARIABLES
    }
    daemon_environment.update(
        CODEX_HOME=str(home),
        CODEX_LAUNCHER_BINARY=environment["CODEX_LAUNCHER_BINARY"],
    )
    log_descriptor = os.open(
        directory / "stderr.log", os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600
    )
    with os.fdopen(log_descriptor, "a") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).with_name("codex_client_host.py")),
            ],
            env=daemon_environment,
            cwd=home,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=log,
            start_new_session=True,
        )
    deadline = time.monotonic() + 5
    while True:
        try:
            request(socket_path, {"method": "status"})
            break
        except (FileNotFoundError, ConnectionRefusedError):
            if process.poll() is not None or time.monotonic() >= deadline:
                raise RuntimeError(
                    f"Codex proxy failed to start; see {directory / 'stderr.log'}"
                )
            time.sleep(0.05)
