from __future__ import annotations

import fcntl
import hashlib
import json
import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


def agent_scope():
    for variable in ("HERDR_PANE_ID", "CODEX_THREAD_ID"):
        if value := os.environ.get(variable):
            return f"{variable}:{value}"
    return None


@dataclass(frozen=True)
class ChromeDevtoolsSession:
    identifier: str
    directory: Path
    automatic_cleanup: bool

    @classmethod
    def current(cls, home_directory):
        scope = agent_scope()
        identifier = hashlib.sha256(
            (scope or f"manual:{os.getuid()}").encode()
        ).hexdigest()[:32]
        state_home = Path(
            os.environ.get("XDG_STATE_HOME", str(home_directory / ".local/state"))
        )
        return cls(
            identifier,
            state_home / "chrome-devtools-cli/sessions",
            scope is not None,
        )

    @property
    def state_file(self):
        return self.directory / f"{self.identifier}.json"

    @property
    def pid_file(self):
        name = f"chrome-devtools-mcp-{self.identifier}"
        if runtime_directory := os.environ.get("XDG_RUNTIME_DIR"):
            return Path(runtime_directory) / name / "daemon.pid"
        return Path("/tmp") / f"{name}-{os.getuid()}" / "daemon.pid"

    def running(self):
        try:
            process_identifier = int(self.pid_file.read_text())
            if process_identifier <= 0:
                return False
            os.kill(process_identifier, 0)
        except (OSError, ValueError):
            return False
        return True

    def mode(self):
        try:
            mode = json.loads(self.state_file.read_text()).get("mode")
        except (OSError, ValueError, AttributeError):
            return "attached"
        return mode if mode in ("attached", "headless") else "attached"

    def require_current_worker(self, upstream_executable):
        if self.mode() == "headless":
            return
        try:
            recorded = json.loads(self.state_file.read_text()).get("upstreamExecutable")
        except (OSError, ValueError, AttributeError):
            recorded = None
        if recorded != upstream_executable:
            raise RuntimeError(
                "Refusing to reuse an older attached worker; its owner must stop it "
                "and obtain scoped approval for a new connection"
            )

    def record_mode(self, mode, upstream_executable=None):
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        temporary_file = self.state_file.with_suffix(".tmp")
        temporary_file.write_text(
            json.dumps({"mode": mode, "upstreamExecutable": upstream_executable})
        )
        temporary_file.replace(self.state_file)

    def clear(self):
        self.state_file.unlink(missing_ok=True)

    @contextmanager
    def locked(self):
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        with (self.directory / f"{self.identifier}.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError("This Chrome DevTools worker is busy") from None
            yield

    @contextmanager
    def attached_locked(self, required=True):
        if not required or self.mode() == "headless":
            yield
            return
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        with (self.directory.parent / "attached.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError(
                    "Attached Chrome is busy; reuse its owning task instead of starting another connection"
                ) from None
            os.set_inheritable(lock.fileno(), True)
            yield
