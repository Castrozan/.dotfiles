import os
import signal
import shlex
import subprocess
import sys
import time

import pytest

from exclusive_run_lock_support import (
    EXCLUSIVE_RUN_LOCK_HELPER_PATH,
    run_bash_acquire_then_exit,
    stop_process_group,
    wait_until_path_exists,
)

EXCLUSIVE_RUN_SCOPE_PATH = EXCLUSIVE_RUN_LOCK_HELPER_PATH.with_name(
    "exclusive_run_scope.py"
)


def build_scoped_program(lock_name, command):
    return f'''set -Eeuo pipefail
source "{EXCLUSIVE_RUN_LOCK_HELPER_PATH}"
acquire_exclusive_run_lock_or_emit_retry_instructions "{lock_name}" 60
exec "{sys.executable}" "{EXCLUSIVE_RUN_SCOPE_PATH}" "$DOTFILES_EXCLUSIVE_RUN_LOCK_FILE_DESCRIPTOR" {shlex.join(command)}
'''


def wait_for_group_exit(process_group, timeout_seconds=5):
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            os.killpg(process_group, 0)
        except ProcessLookupError:
            return
        time.sleep(0.01)
    raise TimeoutError(f"process group {process_group} did not exit")


@pytest.mark.parametrize("termination_target", ["scope", "driver"])
@pytest.mark.parametrize("termination_signal", [signal.SIGTERM, signal.SIGKILL])
def test_termination_keeps_ownership_until_close_fds_grandchild_finishes(
    unique_lock_name_with_cleanup, tmp_path, termination_target, termination_signal
):
    child_started = tmp_path / "child-started"
    child_release = tmp_path / "child-release"
    driver_process_id = tmp_path / "driver-process-id"
    driver = tmp_path / "native_driver.py"
    child_command = (
        f'trap "" TERM; touch "{child_started}"; '
        f'while [[ ! -f "{child_release}" ]]; do sleep 0.01; done'
    )
    driver.write_text(
        "import os\nimport subprocess\nfrom pathlib import Path\n"
        f"Path({str(driver_process_id)!r}).write_text(str(os.getpid()))\n"
        f"subprocess.run(['bash', '-c', {child_command!r}], close_fds=True)\n"
    )
    program = build_scoped_program(
        unique_lock_name_with_cleanup, [sys.executable, str(driver)]
    )
    holder = subprocess.Popen(["bash", "-c", program], start_new_session=True)
    process_group = None
    try:
        wait_until_path_exists(child_started)
        process_group = int(driver_process_id.read_text())
        target = holder.pid if termination_target == "scope" else process_group
        os.kill(target, termination_signal)
        if termination_target == "scope" and termination_signal == signal.SIGKILL:
            holder.wait(timeout=5)
        completed = run_bash_acquire_then_exit(unique_lock_name_with_cleanup)
        assert completed.returncode == 99, completed.stderr
        child_release.touch()
        holder.wait(timeout=5)
        wait_for_group_exit(process_group)
        completed = run_bash_acquire_then_exit(unique_lock_name_with_cleanup)
        assert completed.returncode == 0, completed.stderr
    finally:
        if process_group is not None:
            try:
                os.killpg(process_group, signal.SIGKILL)
            except ProcessLookupError:
                pass
        stop_process_group(holder)


def test_exec_preserves_ownership(unique_lock_name_with_cleanup, tmp_path):
    started = tmp_path / "exec-started"
    release = tmp_path / "exec-release"
    worker = tmp_path / "worker"
    worker.write_text(
        f'touch "{started}"; while [[ ! -f "{release}" ]]; do sleep 0.01; done'
    )
    command = ["bash", "-c", 'exec bash "$1"', "scoped-worker", str(worker)]
    holder = subprocess.Popen(
        ["bash", "-c", build_scoped_program(unique_lock_name_with_cleanup, command)],
        start_new_session=True,
    )
    try:
        wait_until_path_exists(started)
        completed = run_bash_acquire_then_exit(unique_lock_name_with_cleanup)
        assert completed.returncode == 99, completed.stderr
        release.touch()
        holder.wait(timeout=5)
        completed = run_bash_acquire_then_exit(unique_lock_name_with_cleanup)
        assert completed.returncode == 0, completed.stderr
    finally:
        stop_process_group(holder)


@pytest.mark.parametrize("exit_status", [0, 42])
def test_scope_preserves_command_status(unique_lock_name_with_cleanup, exit_status):
    completed = subprocess.run(
        [
            "bash",
            "-c",
            build_scoped_program(
                unique_lock_name_with_cleanup, ["bash", "-c", f"exit {exit_status}"]
            ),
        ],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert completed.returncode == exit_status, completed.stderr


def test_nested_acquisition_with_an_inherited_descriptor_fails_fast(
    unique_lock_name_with_cleanup,
):
    nested_command = (
        f'source "{EXCLUSIVE_RUN_LOCK_HELPER_PATH}"\n'
        f'acquire_exclusive_run_lock_or_emit_retry_instructions "{unique_lock_name_with_cleanup}" 60'
    )
    completed = subprocess.run(
        [
            "bash",
            "-c",
            build_scoped_program(
                unique_lock_name_with_cleanup, ["bash", "-c", nested_command]
            ),
        ],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert completed.returncode == 99, completed.stderr
    assert "LOCKED_BY_CONCURRENT_RUN" in completed.stderr
    assert run_bash_acquire_then_exit(unique_lock_name_with_cleanup).returncode == 0
