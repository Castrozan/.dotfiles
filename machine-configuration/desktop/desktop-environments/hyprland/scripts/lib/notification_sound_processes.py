import os
import signal
import subprocess
from pathlib import Path


def is_pid_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def read_pid_from_file(pid_file: Path) -> int | None:
    if not pid_file.is_file():
        return None
    try:
        return int(pid_file.read_text().strip())
    except (ValueError, OSError):
        return None


def stop_process_by_pid_file(pid_file: Path) -> None:
    pid = read_pid_from_file(pid_file)
    if pid is None:
        return
    try:
        subprocess.run(["pkill", "-P", str(pid)], capture_output=True)
        os.kill(pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        pass
    pid_file.unlink(missing_ok=True)
