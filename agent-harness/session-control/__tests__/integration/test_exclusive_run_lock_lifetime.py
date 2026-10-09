import os
import signal
import subprocess

import pytest

from exclusive_run_lock_support import (
    EXCLUSIVE_RUN_LOCK_HELPER_PATH,
    run_bash_acquire_then_exit,
    stop_process_group,
    wait_until_path_exists,
)


def test_contender_cannot_reclaim_owner_before_metadata_is_written(
    unique_lock_name_with_cleanup, tmp_path
):
    lock_name = unique_lock_name_with_cleanup
    metadata_started = tmp_path / "metadata-started"
    metadata_continue = tmp_path / "metadata-continue"
    program = f"""
set -Eeuo pipefail
source "{EXCLUSIVE_RUN_LOCK_HELPER_PATH}"
eval "$(declare -f _write_lock_owner_metadata | sed '1s/_write_lock_owner_metadata/write_original_lock_owner_metadata/')"
_write_lock_owner_metadata() {{
    touch "{metadata_started}"
    while [[ ! -f "{metadata_continue}" ]]; do sleep 0.01; done
    write_original_lock_owner_metadata "$@"
}}
acquire_exclusive_run_lock_or_emit_retry_instructions "{lock_name}" 60
sleep 30
"""
    holder = subprocess.Popen(["bash", "-c", program], start_new_session=True)
    try:
        wait_until_path_exists(metadata_started)
        completed = run_bash_acquire_then_exit(lock_name)
        assert completed.returncode == 99, completed.stderr
    finally:
        metadata_continue.touch()
        stop_process_group(holder)


@pytest.mark.parametrize("termination_signal", [signal.SIGTERM, signal.SIGKILL])
def test_owner_termination_does_not_release_a_running_child(
    unique_lock_name_with_cleanup, tmp_path, termination_signal
):
    lock_name = unique_lock_name_with_cleanup
    child_started = tmp_path / "child-started"
    child_continue = tmp_path / "child-continue"
    child_finished = tmp_path / "child-finished"
    program = f"""
set -Eeuo pipefail
source "{EXCLUSIVE_RUN_LOCK_HELPER_PATH}"
acquire_exclusive_run_lock_or_emit_retry_instructions "{lock_name}" 60
bash -c 'touch "{child_started}"; while [[ ! -f "{child_continue}" ]]; do sleep 0.01; done; touch "{child_finished}"' &
wait
"""
    holder = subprocess.Popen(["bash", "-c", program], start_new_session=True)
    try:
        wait_until_path_exists(child_started)
        holder.send_signal(termination_signal)
        holder.wait(timeout=5)
        completed = run_bash_acquire_then_exit(lock_name)
        assert completed.returncode == 99, completed.stderr
        child_continue.touch()
        wait_until_path_exists(child_finished)
        completed = run_bash_acquire_then_exit(lock_name)
        assert completed.returncode == 0, completed.stderr
    finally:
        stop_process_group(holder)


def test_child_termination_does_not_release_the_living_owner(
    unique_lock_name_with_cleanup, tmp_path
):
    lock_name = unique_lock_name_with_cleanup
    child_started = tmp_path / "child-started"
    program = f"""
set -Eeuo pipefail
source "{EXCLUSIVE_RUN_LOCK_HELPER_PATH}"
acquire_exclusive_run_lock_or_emit_retry_instructions "{lock_name}" 60
sleep 30 &
echo $! > "{child_started}"
wait || true
sleep 30
"""
    holder = subprocess.Popen(["bash", "-c", program], start_new_session=True)
    try:
        wait_until_path_exists(child_started)
        os.kill(int(child_started.read_text()), signal.SIGKILL)
        completed = run_bash_acquire_then_exit(lock_name)
        assert completed.returncode == 99, completed.stderr
    finally:
        stop_process_group(holder)


def test_existing_exit_trap_survives_acquisition(
    unique_lock_name_with_cleanup, tmp_path
):
    marker = tmp_path / "exit-trap-ran"
    completed = subprocess.run(
        [
            "bash",
            "-c",
            f'''source "{EXCLUSIVE_RUN_LOCK_HELPER_PATH}"
trap 'touch "{marker}"' EXIT
acquire_exclusive_run_lock_or_emit_retry_instructions "{unique_lock_name_with_cleanup}" 60
''',
        ],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert completed.returncode == 0, completed.stderr
    assert marker.exists()
