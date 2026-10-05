import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time

from codex_app_server_client import CodexAppServerClient
from profile_connection import profile_connection_path
from session_server_configuration import server_configuration_for


def wait_for_session_server(server, socket_path: Path) -> None:
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError("Codex private session server exited during startup")
        if socket_path.is_socket():
            try:
                with CodexAppServerClient(
                    str(socket_path), min(0.25, deadline - time.monotonic())
                ):
                    return
            except Exception:
                pass
        time.sleep(0.05)
    raise TimeoutError("Codex private session server did not become ready within 5s")


def process_group_exists(process_identifier: int) -> bool:
    try:
        os.killpg(process_identifier, 0)
    except ProcessLookupError:
        return False
    return True


def stop_process(process, *, process_group: bool = False) -> None:
    if process is None:
        return
    deadline = time.monotonic() + 1.0
    if process_group:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    elif process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=1.0)
    except subprocess.TimeoutExpired:
        if process_group:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()
        process.wait()
    if process_group:
        while time.monotonic() < deadline and process_group_exists(process.pid):
            time.sleep(0.05)
        if process_group_exists(process.pid):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def stop_client_when_server_exits(server, client) -> None:
    server.wait()
    if client.poll() is None:
        client.terminate()


def run_private_session(arguments: list[str]) -> int:
    managed_permission_arguments = [
        "--sandbox",
        "danger-full-access",
        "--ask-for-approval",
        "never",
    ]
    managed_permissions = arguments[:4] == managed_permission_arguments
    client_arguments = arguments[4:] if managed_permissions else arguments
    configuration = server_configuration_for(client_arguments)
    server_arguments = list(configuration.arguments)
    if managed_permissions:
        server_arguments.extend(
            [
                "-c",
                'sandbox_mode="danger-full-access"',
                "-c",
                'approval_policy="never"',
            ]
        )
    binary = os.environ["CODEX_LAUNCHER_BINARY"]
    with tempfile.TemporaryDirectory(prefix="codex-session-", dir="/tmp") as directory:
        socket_path = Path(directory) / "server.sock"
        endpoint = f"unix://{socket_path}"
        environment = os.environ.copy()
        environment.pop("CODEX_THREAD_ID", None)
        if environment.get("CODEX_HOME"):
            environment["CODEX_HOME"] = str(Path(environment["CODEX_HOME"]).resolve())
        environment["CODEX_SESSION_SOCKET_PATH"] = str(socket_path)
        server = None
        client = None
        try:
            server = subprocess.Popen(
                [binary, *server_arguments, "app-server", "--listen", endpoint],
                cwd=configuration.working_directory,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                start_new_session=True,
            )
            wait_for_session_server(server, socket_path)
            with profile_connection_path(
                socket_path, configuration.profile_path
            ) as client_path:
                client = subprocess.Popen(
                    [binary, "--remote", f"unix://{client_path}", *client_arguments],
                    env=environment,
                )
                threading.Thread(
                    target=stop_client_when_server_exits,
                    args=(server, client),
                    daemon=True,
                ).start()
                exit_status = client.wait()
                return exit_status if exit_status >= 0 else 128 - exit_status
        finally:
            stop_process(client)
            stop_process(server, process_group=True)


def keep_interrupt_with_terminal_client(signal_number, frame) -> None:
    pass


def exit_on_shutdown(signal_number, frame) -> None:
    raise SystemExit(128 + signal_number)


def main() -> int:
    previous_handlers = {
        signal_number: signal.getsignal(signal_number)
        for signal_number in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)
    }
    signal.signal(signal.SIGINT, keep_interrupt_with_terminal_client)
    signal.signal(signal.SIGTERM, exit_on_shutdown)
    signal.signal(signal.SIGHUP, exit_on_shutdown)
    try:
        return run_private_session(sys.argv[1:])
    except (OSError, ValueError, RuntimeError, TimeoutError) as error:
        print(str(error), file=sys.stderr)
        return 1
    finally:
        for signal_number, handler in previous_handlers.items():
            signal.signal(signal_number, handler)


if __name__ == "__main__":
    sys.exit(main())
