import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

import pytest

SCRIPT_PATH = (
    pathlib.Path(__file__).resolve().parents[2] / "scripts" / "run-herdr-client.sh"
)
BASH_EXECUTABLE = shutil.which("bash")

pytestmark = pytest.mark.skipif(
    not sys.platform.startswith("linux"),
    reason="the recorded server is verified through /proc",
)


class ClientHarness:
    def __init__(self, tmp_path):
        self.working_directory = tmp_path / "working-directory"
        self.working_directory.mkdir()
        self.state_home = tmp_path / "state"
        self.record_path = self.state_home / "herdr" / "running-server-client"
        self.socket_path = tmp_path / "herdr.sock"
        self.socket_path.write_text("")
        self.installed_executable = self._bash_copy(tmp_path / "installed")
        self.other_executable = self._bash_copy(tmp_path / "other")
        self.selector_log = tmp_path / "selector.log"
        self.selector_directory = tmp_path / "selector-bin"
        self.selector_directory.mkdir()
        self._write_working_directory_script(
            "status",
            f"echo '{self._compact_server_status()}'",
        )
        self._write_working_directory_script("pane", 'echo "ran-by:$BASH"')
        selector = self.selector_directory / "select-herdr-client"
        selector.write_text(
            "#!/bin/sh\n"
            f'echo "$HERDR_RUNNING_SERVER_RECORD" >> {self.selector_log}\n'
            f"echo {self.other_executable}\n"
        )
        selector.chmod(0o755)
        self.held_processes = []

    def _compact_server_status(self):
        return json.dumps(
            {"running": True, "socket": str(self.socket_path)},
            separators=(",", ":"),
        )

    def _bash_copy(self, directory):
        executable = directory / "bin" / "herdr"
        executable.parent.mkdir(parents=True)
        shutil.copy2(BASH_EXECUTABLE, executable)
        return executable

    def _write_working_directory_script(self, name, body):
        (self.working_directory / name).write_text(body + "\n")

    def hold_process_running(self, executable):
        process = subprocess.Popen(
            [str(executable), "-c", "read -r _"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
        )
        self.held_processes.append(process)
        return process.pid

    def record_running_server(self, process_identifier):
        self.record_path.parent.mkdir(parents=True, exist_ok=True)
        self.record_path.write_text(f"{self.socket_path}\n{process_identifier}\n")
        newer_than_socket = time.time() + 10
        os.utime(self.record_path, (newer_than_socket, newer_than_socket))

    def run_client(self):
        environment = dict(os.environ)
        environment["XDG_STATE_HOME"] = str(self.state_home)
        environment["PATH"] = (
            f"{self.selector_directory}{os.pathsep}{environment['PATH']}"
        )
        return subprocess.run(
            [
                BASH_EXECUTABLE,
                "-euo",
                "pipefail",
                str(SCRIPT_PATH),
                str(self.installed_executable),
                "pane",
            ],
            capture_output=True,
            text=True,
            check=True,
            cwd=self.working_directory,
            env=environment,
        ).stdout.strip()

    def selector_was_consulted(self):
        return self.selector_log.exists()

    def release_held_processes(self):
        for process in self.held_processes:
            process.stdin.close()
            process.wait(timeout=5)


@pytest.fixture
def client_harness(tmp_path):
    harness = ClientHarness(tmp_path)
    yield harness
    harness.release_held_processes()


def test_recorded_server_running_the_installed_executable_skips_the_selector(
    client_harness,
):
    client_harness.record_running_server(
        client_harness.hold_process_running(client_harness.installed_executable)
    )

    output = client_harness.run_client()

    assert output == f"ran-by:{client_harness.installed_executable}"
    assert not client_harness.selector_was_consulted()


def test_missing_record_consults_the_selector_and_names_the_record(client_harness):
    output = client_harness.run_client()

    assert output == f"ran-by:{client_harness.other_executable}"
    assert client_harness.selector_log.read_text().strip() == str(
        client_harness.record_path
    )


def test_socket_bound_after_the_record_consults_the_selector(client_harness):
    client_harness.record_running_server(
        client_harness.hold_process_running(client_harness.installed_executable)
    )
    rebound_after_record = time.time() + 20
    os.utime(client_harness.socket_path, (rebound_after_record, rebound_after_record))

    output = client_harness.run_client()

    assert output == f"ran-by:{client_harness.other_executable}"


def test_recorded_process_running_another_executable_consults_the_selector(
    client_harness,
):
    client_harness.record_running_server(
        client_harness.hold_process_running(client_harness.other_executable)
    )

    output = client_harness.run_client()

    assert output == f"ran-by:{client_harness.other_executable}"
