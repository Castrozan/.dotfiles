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

    def record_mode(self, mode):
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        temporary_file = self.state_file.with_suffix(".tmp")
        temporary_file.write_text(json.dumps({"mode": mode}))
        temporary_file.replace(self.state_file)

    def clear(self):
        self.state_file.unlink(missing_ok=True)

    @contextmanager
    def locked(self):
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        with (self.directory / f"{self.identifier}.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            yield
