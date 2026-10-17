import fcntl
import os
import shutil
import socket
import sys
import tempfile
from pathlib import Path


def require_closed_profile(source):
    singleton = source / "SingletonLock"
    if singleton.is_symlink():
        owner, _, process = os.readlink(singleton).rpartition("-")
        if owner == socket.gethostname() and process.isdigit():
            try:
                os.kill(int(process), 0)
            except ProcessLookupError:
                pass
            else:
                raise RuntimeError("Close the source profile before importing it")


def import_profile(source, destination):
    if destination.exists() or not source.is_dir():
        return
    require_closed_profile(source)
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = Path(
        tempfile.mkdtemp(prefix=".profile-import-", dir=destination.parent)
    )
    try:
        shutil.copytree(
            source,
            temporary,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(
                "Singleton*", ".pinchtab-state", "DevToolsActivePort"
            ),
        )
        temporary.chmod(0o700)
        temporary.rename(destination)
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


def main():
    source, destination = Path(sys.argv[1]), Path(sys.argv[2])
    if destination.exists() or not source.is_dir():
        return
    state = (
        Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "opencli"
    )
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (state / "job.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        import_profile(source, destination)


if __name__ == "__main__":
    main()
