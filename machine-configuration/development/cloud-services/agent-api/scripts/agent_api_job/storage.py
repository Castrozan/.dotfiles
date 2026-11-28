import json
import os
import stat
from pathlib import Path

from agent_api_job.errors import JobError


def state_root():
    configured = os.environ.get("AGENT_API_JOB_STATE")
    if configured:
        return Path(configured)
    base = os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state"
    return Path(base) / "agent-api-job"


def private_directory(path):
    path.mkdir(parents=True, mode=0o700, exist_ok=True)
    metadata = path.stat()
    if metadata.st_uid != os.geteuid() or stat.S_IMODE(metadata.st_mode) & 0o077:
        raise JobError("state_unavailable")
    return path


def write_json(path, value):
    temporary = path.with_name(path.name + ".pending")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(descriptor, "w") as stream:
            json.dump(value, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def read_json(path):
    try:
        return json.loads(path.read_bytes())
    except FileNotFoundError:
        return None
