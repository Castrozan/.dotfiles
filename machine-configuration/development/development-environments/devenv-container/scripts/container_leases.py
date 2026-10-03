import fcntl
import json
import time
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def file_lock(path, exclusive=True, blocking=True):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open("a+") as handle:
        operation = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        if not blocking:
            operation |= fcntl.LOCK_NB
        fcntl.flock(handle, operation)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def project_lock(project, name="lifecycle", exclusive=True, blocking=True):
    return file_lock(project.state_directory / f"{name}.lock", exclusive, blocking)


def runtime_lock(policy, blocking=True):
    return file_lock(Path(policy.state_root) / "runtime.lock", blocking=blocking)


def record_use(project):
    state_path = project.state_directory / "project.json"
    temporary_path = state_path.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(
            {
                "directory": str(project.directory),
                "last_used": time.time(),
            }
        )
    )
    temporary_path.replace(state_path)


def project_is_idle(project, timeout_seconds, now=None):
    state = json.loads((project.state_directory / "project.json").read_text())
    return (time.time() if now is None else now) - state["last_used"] >= timeout_seconds
