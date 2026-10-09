import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time


TESTS_DIRECTORY = Path(__file__).resolve().parents[2]
LAUNCHER = TESTS_DIRECTORY.parent / "scripts/session_server/launch_private_session.py"
STUB = TESTS_DIRECTORY / "support/private_session_lifecycle_stub.py"
OWNED_ROLES = ("launcher", "server", "client", "worker-one", "worker-two")


def wait_until(predicate, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.02)
    raise TimeoutError("private session fixture did not reach its expected state")


def process_is_alive(identity):
    process_identifier = identity["process_identifier"]
    if sys.platform == "linux":
        try:
            fields = (
                Path(f"/proc/{process_identifier}/stat")
                .read_text()
                .rsplit(")", 1)[1]
                .split()
            )
        except FileNotFoundError:
            return False
        return int(fields[19]) == identity["birth"] and fields[0] != "Z"
    try:
        os.kill(process_identifier, 0)
    except ProcessLookupError:
        return False
    return True


class PrivateSessionFixture:
    def __init__(self, directory):
        self.directory = directory
        self.environment = {
            name: value
            for name, value in os.environ.items()
            if not name.startswith(("HERDR_", "CLAWDE_", "CODEX_"))
        }
        binary = directory / "codex-stub"
        binary.write_text(f"#!{sys.executable}\n" + STUB.read_text())
        binary.chmod(0o755)
        self.environment["CODEX_LAUNCHER_BINARY"] = str(binary)
        self.environment["CODEX_TEST_STATE_DIRECTORY"] = str(directory)
        self.environment["PYTHONPATH"] = os.pathsep.join(
            (
                str(LAUNCHER.parent),
                str(TESTS_DIRECTORY.parents[2] / "hooks/runtime/common"),
            )
        )
        self.processes = []
        self.identities = {}
        self.herdr = None
        self.pane = None

    def run_herdr(self, *arguments):
        result = subprocess.run(
            [self.herdr, "--session", "ownership", *arguments],
            env=self.environment,
            capture_output=True,
            text=True,
            timeout=5.0,
            check=True,
        )
        if arguments[:2] in (("pane", "run"), ("pane", "close"), ("server", "stop")):
            return None
        return json.loads(result.stdout)["result"]

    def start(self, native=False):
        peer = subprocess.Popen(
            [sys.executable, str(STUB), "peer"],
            env=self.environment,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.processes.append(peer)
        if native:
            self.start_native()
        else:
            self.processes.append(
                subprocess.Popen(
                    [sys.executable, str(LAUNCHER)],
                    env=self.environment,
                    start_new_session=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            )
        wait_until(
            lambda: all(
                (self.directory / f"{role}.json").exists()
                for role in (*OWNED_ROLES, "peer")
            )
        )
        self.identities = {
            role: json.loads((self.directory / f"{role}.json").read_text())
            for role in (*OWNED_ROLES, "peer")
        }

    def start_native(self):
        self.herdr = shutil.which("herdr")
        self.environment["XDG_CONFIG_HOME"] = str(self.directory / "config")
        self.environment["XDG_STATE_HOME"] = str(self.directory / "state")
        configuration = self.directory / "config.toml"
        shell = self.directory / "shell"
        shell.write_text(f"#!{shutil.which('bash')}\nexec bash --noprofile --norc\n")
        shell.chmod(0o755)
        configuration.write_text(
            f"onboarding = false\n[terminal]\ndefault_shell = {json.dumps(str(shell))}\n"
            'shell_mode = "non_login"\n[update]\nversion_check = false\nmanifest_check = false\n'
            "[session]\nresume_agents_on_restore = false\n[ui.sound]\nenabled = false\n"
        )
        self.environment["HERDR_CONFIG_PATH"] = str(configuration)
        self.processes.append(
            subprocess.Popen(
                [self.herdr, "--session", "ownership", "server"],
                env=self.environment,
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        )
        socket = self.directory / "config/herdr/sessions/ownership/herdr.sock"
        wait_until(socket.is_socket)
        workspace = self.run_herdr(
            "workspace",
            "create",
            "--cwd",
            str(self.directory),
            "--label",
            "ownership-fixture",
            "--no-focus",
        )
        self.pane = workspace["root_pane"]["pane_id"]
        self.run_herdr("pane", "run", self.pane, "exec", sys.executable, str(LAUNCHER))

    def close(self):
        try:
            for path in self.directory.glob("*.json"):
                identity = json.loads(path.read_text())
                if process_is_alive(identity):
                    try:
                        os.kill(identity["process_identifier"], signal.SIGKILL)
                    except ProcessLookupError:
                        pass
            if self.herdr:
                self.run_herdr("server", "stop")
        finally:
            for process in self.processes:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=5.0)
