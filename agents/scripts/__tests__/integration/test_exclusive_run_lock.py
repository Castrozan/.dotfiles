import os
import subprocess
import time
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
EXCLUSIVE_RUN_LOCK_HELPER_PATH = REPO_ROOT / "agents/scripts/exclusive-run-lock.sh"


def build_unique_lock_name():
    return f"test-exclrun-{uuid.uuid4().hex[:12]}"


def build_lock_directory_path_for(lock_name):
    return Path(f"/tmp/dotfiles-{lock_name}.lock.d")


def wait_until_lock_directory_owner_metadata_exists(lock_name, timeout_seconds=5):
    deadline = time.time() + timeout_seconds
    owner_metadata_path = build_lock_directory_path_for(lock_name) / "owner"
    while time.time() < deadline:
        if owner_metadata_path.exists():
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


@pytest.fixture
def unique_lock_name_with_cleanup():
    name = build_unique_lock_name()
    yield name
    lock_directory_path = build_lock_directory_path_for(name)
    if lock_directory_path.exists():
        subprocess.run(["rm", "-rf", str(lock_directory_path)], check=False)


def test_acquires_lock_and_releases_on_exit_when_directory_does_not_exist(
    unique_lock_name_with_cleanup,
):
    completed = run_bash_acquire_then_exit(unique_lock_name_with_cleanup)
    assert completed.returncode == 0, completed.stderr
    assert not build_lock_directory_path_for(unique_lock_name_with_cleanup).exists()


def test_second_concurrent_acquire_exits_99_with_contention_instructions(
    unique_lock_name_with_cleanup,
):
    holder_program = build_bash_program_that_acquires_then_sleeps(
        unique_lock_name_with_cleanup, sleep_seconds=5
    )
    with subprocess.Popen(
        ["bash", "-c", holder_program],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as holder:
        try:
            wait_until_lock_directory_owner_metadata_exists(
                unique_lock_name_with_cleanup
            )
            completed = run_bash_acquire_then_exit(unique_lock_name_with_cleanup)
            assert completed.returncode == 99
            assert "LOCKED_BY_CONCURRENT_RUN" in completed.stderr
            assert "ScheduleWakeup(delaySeconds=" in completed.stderr
            assert unique_lock_name_with_cleanup in completed.stderr
        finally:
            holder.terminate()
            holder.wait(timeout=5)


def test_stale_lock_directory_with_dead_owner_pid_is_reclaimed(
    unique_lock_name_with_cleanup,
):
    stale_lock_directory_path = build_lock_directory_path_for(
        unique_lock_name_with_cleanup
    )
    stale_lock_directory_path.mkdir(parents=True)
    (stale_lock_directory_path / "owner").write_text(
        "pid=99999999\nstarted_epoch=1\nscript=stale\ntypical_duration_seconds=60\nlog_path=\n"
    )
    completed = run_bash_acquire_then_exit(unique_lock_name_with_cleanup)
    assert completed.returncode == 0, completed.stderr
    assert not stale_lock_directory_path.exists()


def test_bypass_environment_variable_skips_locking_entirely(
    unique_lock_name_with_cleanup,
):
    holder_program = build_bash_program_that_acquires_then_sleeps(
        unique_lock_name_with_cleanup, sleep_seconds=5
    )
    with subprocess.Popen(
        ["bash", "-c", holder_program],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as holder:
        try:
            wait_until_lock_directory_owner_metadata_exists(
                unique_lock_name_with_cleanup
            )
            completed = run_bash_acquire_then_exit(
                unique_lock_name_with_cleanup,
                extra_env={"DOTFILES_BYPASS_EXCLUSIVE_RUN_LOCK": "1"},
            )
            assert completed.returncode == 0, completed.stderr
        finally:
            holder.terminate()
            holder.wait(timeout=5)
