import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

import pytest

SCRIPTS_DIRECTORY = pathlib.Path(__file__).resolve().parents[2] / "scripts"
BASH_EXECUTABLE = shutil.which("bash")
CHILD_TIMEOUT_SECONDS = 30

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
        self._set_modification_time(self.socket_path, time.time() - 100)
        self.installed_executable = self._bash_copy(tmp_path / "installed")
        self.other_executable = self._bash_copy(tmp_path / "other")
        self.tool_directory = tmp_path / "tools"
        self.tool_directory.mkdir()
        self.lookup_log = tmp_path / "lookups.log"
        self.held_processes = []
        server_status = json.dumps(
            {"running": True, "socket": str(self.socket_path)}, separators=(",", ":")
        )
        (self.working_directory / "status").write_text(f"echo '{server_status}'\n")
        (self.working_directory / "pane").write_text('echo "ran-by:$BASH"\n')
        self._write_tool(
            "select-herdr-client",
            f'exec {sys.executable} {SCRIPTS_DIRECTORY}/select-herdr-client.py "$@"\n',
        )
        self.server_process_identifier = self.hold_process_running(
            self.installed_executable
        )
        self._write_tool(
            "lsof",
            f"echo lookup >> {self.lookup_log}\n"
            'case " $* " in\n'
            f'*" -t "*) echo {self.server_process_identifier} ;;\n'
            f'*) printf "p%s\\nn%s\\n" {self.server_process_identifier} '
            f"{self.installed_executable} ;;\n"
            "esac\n",
        )

    def _set_modification_time(self, path, timestamp):
        os.utime(path, (timestamp, timestamp))

    def _bash_copy(self, directory):
        executable = directory / "bin" / "herdr"
        executable.parent.mkdir(parents=True)
        shutil.copy2(BASH_EXECUTABLE, executable)
        return executable

    def _write_tool(self, name, body):
        tool = self.tool_directory / name
        tool.write_text(f"#!{BASH_EXECUTABLE}\n{body}")
        tool.chmod(0o755)

    def hold_process_running(self, executable):
        process = subprocess.Popen(
            [str(executable), "-c", "read -r _"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
        )
        self.held_processes.append(process)
        return process.pid

    def run_client(self):
        environment = dict(os.environ)
        environment["XDG_STATE_HOME"] = str(self.state_home)
        environment["PATH"] = f"{self.tool_directory}{os.pathsep}{environment['PATH']}"
        return subprocess.run(
            [
                BASH_EXECUTABLE,
                "-euo",
                "pipefail",
                str(SCRIPTS_DIRECTORY / "run-herdr-client.sh"),
                str(self.installed_executable),
                "pane",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=CHILD_TIMEOUT_SECONDS,
            cwd=self.working_directory,
            env=environment,
        ).stdout.strip()

    def run_client_counting_lookups(self):
        lookups_before = self.lookup_count()
        output = self.run_client()
        return output, self.lookup_count() - lookups_before

    def lookup_count(self):
        if not self.lookup_log.exists():
            return 0
        return len(self.lookup_log.read_text().splitlines())

    def rebind_socket(self):
        self._set_modification_time(self.socket_path, time.time() + 100)

    def record_process_running_another_executable(self):
        other_process_identifier = self.hold_process_running(self.other_executable)
        self.record_path.write_text(f"{self.socket_path}\n{other_process_identifier}\n")

    def release_held_processes(self):
        for process in self.held_processes:
            process.stdin.close()
            process.wait(timeout=CHILD_TIMEOUT_SECONDS)


@pytest.fixture
def client_harness(tmp_path):
    harness = ClientHarness(tmp_path)
    yield harness
    harness.release_held_processes()


def test_server_resolved_once_is_not_looked_up_again_while_it_stays_unchanged(
    client_harness,
):
    first_output, first_lookups = client_harness.run_client_counting_lookups()
    second_output, second_lookups = client_harness.run_client_counting_lookups()

    expected_output = f"ran-by:{client_harness.installed_executable}"
    assert (first_output, second_output) == (expected_output, expected_output)
    assert first_lookups > 0
    assert second_lookups == 0


@pytest.mark.parametrize(
    "invalidate_record",
    [
        lambda harness: harness.record_path.unlink(),
        lambda harness: harness.rebind_socket(),
        lambda harness: harness.record_process_running_another_executable(),
    ],
    ids=["record-removed", "socket-rebound", "process-runs-another-executable"],
)
def test_server_is_looked_up_again_when_its_record_no_longer_proves_it(
    client_harness, invalidate_record
):
    client_harness.run_client()
    invalidate_record(client_harness)

    _, lookups = client_harness.run_client_counting_lookups()

    assert lookups > 0
