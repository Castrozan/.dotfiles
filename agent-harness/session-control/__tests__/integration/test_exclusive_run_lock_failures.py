import os
import shutil
import subprocess

import pytest

from exclusive_run_lock_support import (
    EXCLUSIVE_RUN_LOCK_HELPER_PATH,
    build_lock_file_path_for,
    run_bash_acquire_then_exit,
    stop_process_group,
    wait_until_path_exists,
)


@pytest.mark.parametrize("file_kind", ["directory", "symlink", "fifo"])
def test_invalid_lock_file_fails_closed(
    unique_lock_name_with_cleanup, tmp_path, file_kind
):
    lock_path = build_lock_file_path_for(unique_lock_name_with_cleanup)
    if file_kind == "directory":
        lock_path.mkdir()
    elif file_kind == "fifo":
        os.mkfifo(lock_path)
    else:
        target = tmp_path / "target"
        target.write_text("untouched")
        lock_path.symlink_to(target)
    try:
        completed = run_bash_acquire_then_exit(unique_lock_name_with_cleanup)
        assert completed.returncode == 1, completed.stderr
        assert "exclusive run lock unavailable" in completed.stderr
        if file_kind == "symlink":
            assert target.read_text() == "untouched"
    finally:
        if file_kind == "directory":
            lock_path.rmdir()


def test_missing_python_fails_closed(unique_lock_name_with_cleanup, tmp_path):
    completed = subprocess.run(
        [
            shutil.which("bash"),
            "-c",
            f'''source "{EXCLUSIVE_RUN_LOCK_HELPER_PATH}"
acquire_exclusive_run_lock_or_emit_retry_instructions "{unique_lock_name_with_cleanup}" 60
echo UNGUARDED_WORKLOAD
''',
        ],
        env={**os.environ, "PATH": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert completed.returncode == 1, completed.stderr
    assert "UNGUARDED_WORKLOAD" not in completed.stdout


def test_malformed_metadata_cannot_execute_arithmetic_expansions(
    unique_lock_name_with_cleanup, tmp_path
):
    acquired = tmp_path / "acquired"
    injected = tmp_path / "injected"
    lock_name = unique_lock_name_with_cleanup
    program = f'''source "{EXCLUSIVE_RUN_LOCK_HELPER_PATH}"
acquire_exclusive_run_lock_or_emit_retry_instructions "{lock_name}" 60
touch "{acquired}"
sleep 30
'''
    holder = subprocess.Popen(["bash", "-c", program], start_new_session=True)
    try:
        wait_until_path_exists(acquired)
        build_lock_file_path_for(lock_name).write_text(
            f"pid=bad\nstarted_epoch=bad[$(touch {injected})]\n"
            "typical_duration_seconds=999999999999999999999999\n"
        )
        completed = run_bash_acquire_then_exit(lock_name)
        assert completed.returncode == 99, completed.stderr
        assert "in_progress_pid:      unknown" in completed.stderr
        assert "Recommended wait:" in completed.stderr
        assert not injected.exists()
    finally:
        stop_process_group(holder)
