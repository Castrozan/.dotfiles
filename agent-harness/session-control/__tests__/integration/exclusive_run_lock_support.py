import os
import signal
import subprocess
import time
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
EXCLUSIVE_RUN_LOCK_HELPER_PATH = (
    REPO_ROOT / "agent-harness/session-control/exclusive-run-lock.sh"
)


def build_unique_lock_name():
    return f"test-exclrun-{uuid.uuid4().hex[:12]}"


def build_lock_file_path_for(lock_name):
    return Path(os.sep) / "tmp" / f"dotfiles-{lock_name}.lock"


def wait_until_lock_metadata_written(lock_name, timeout_seconds=5):
    deadline = time.time() + timeout_seconds
    owner_metadata_path = build_lock_file_path_for(lock_name)
    while time.time() < deadline:
        if owner_metadata_path.exists() and "pid=" in owner_metadata_path.read_text():
            return
        time.sleep(0.05)
    raise TimeoutError(f"lock {lock_name} not acquired within {timeout_seconds}s")


def build_bash_program_that_acquires_then_sleeps(
    lock_name, sleep_seconds, typical_duration_seconds=60
):
    return f"""
set -Eeuo pipefail
source "{EXCLUSIVE_RUN_LOCK_HELPER_PATH}"
acquire_exclusive_run_lock_or_emit_retry_instructions "{lock_name}" {typical_duration_seconds}
sleep {sleep_seconds}
"""


def run_bash_acquire_then_exit(lock_name, typical_duration_seconds=60, extra_env=None):
    program = build_bash_program_that_acquires_then_sleeps(
        lock_name, sleep_seconds=0, typical_duration_seconds=typical_duration_seconds
    )
    env = {**os.environ, **(extra_env or {})}
    return subprocess.run(
        ["bash", "-c", program],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )


def wait_until_path_exists(path, timeout_seconds=5):
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.01)
    raise TimeoutError(f"{path} did not appear within {timeout_seconds}s")


def stop_process_group(process):
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=5)
