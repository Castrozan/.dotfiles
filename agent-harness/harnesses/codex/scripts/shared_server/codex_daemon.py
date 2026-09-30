import fcntl
import json
import os
from pathlib import Path
import subprocess

from codex_shell_environment import CORE_VARIABLES


class DaemonLease:
    def __init__(self, binary, environment):
        self.binary = binary
        self.home = Path(environment.get("CODEX_HOME", Path.home() / ".codex"))
        self.directory = self.home / "client-context"
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.environment = {
            name: value for name, value in environment.items() if name in CORE_VARIABLES
        }
        self.environment.update(
            CODEX_HOME=str(self.home), DOTFILES_CODEX_SHARED_SERVER="1"
        )
        self.clients = self.open_lock("clients.lock")
        fcntl.flock(self.clients, fcntl.LOCK_SH)

    def open_lock(self, name):
        return os.fdopen(
            os.open(self.directory / name, os.O_CREAT | os.O_RDWR, 0o600), "w"
        )

    def command(self, operation):
        result = subprocess.run(
            [self.binary, "app-server", "daemon", operation],
            env=self.environment,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=75,
        )
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or "Codex daemon failed to start")
        return json.loads(result.stdout)

    def ensure_running(self):
        with self.open_lock("startup.lock") as startup:
            fcntl.flock(startup, fcntl.LOCK_EX)
            result = self.command("start")
            process_path = self.home / "app-server-daemon/daemon.pid"
            process = json.loads(process_path.read_text())
            state_path = self.directory / "daemon.json"
            try:
                state = json.loads(state_path.read_text())
            except (OSError, ValueError):
                state = {}
            if result["status"] != "started" and state != process:
                raise RuntimeError(
                    "The running Codex daemon was started outside the client adapter. "
                    "Stop it before using shared mode, or use --no-daemon."
                )
            if result["appServerVersion"] != result["cliVersion"]:
                fcntl.flock(self.clients, fcntl.LOCK_UN)
                try:
                    fcntl.flock(self.clients, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as error:
                    fcntl.flock(self.clients, fcntl.LOCK_SH)
                    raise RuntimeError(
                        "Codex was upgraded while shared clients are attached. "
                        "Close those clients before launching the new version, or use --no-daemon."
                    ) from error
                try:
                    result = self.command("restart")
                    process = json.loads(process_path.read_text())
                finally:
                    fcntl.flock(self.clients, fcntl.LOCK_SH)
            if result["appServerVersion"] != result["cliVersion"]:
                raise RuntimeError(
                    "The selected daemon package does not match this Codex CLI"
                )
            state_path.write_text(json.dumps(process))
            state_path.chmod(0o600)
            return Path(result["socketPath"])

    def close(self):
        self.clients.close()
