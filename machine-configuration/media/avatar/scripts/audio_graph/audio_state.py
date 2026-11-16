import contextlib
import fcntl
import json
import os
from pathlib import Path


def runtime_directory():
    return (
        Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")) / "avatar"
    )


@contextlib.contextmanager
def exclusive_state():
    directory = runtime_directory()
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (directory / "audio.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield directory / "audio.json"


def read_state(path):
    return json.loads(path.read_text()) if path.exists() else {"modules": []}


def write_state(path, state):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state))
    temporary.chmod(0o600)
    temporary.replace(path)


def matches_module(entry, modules):
    return any(
        module["index"] == entry["index"]
        and module["name"] == entry["name"]
        and module["argument"] == entry["argument"]
        for module in modules
    )
