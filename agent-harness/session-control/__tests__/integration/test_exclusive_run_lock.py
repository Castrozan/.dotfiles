import subprocess

from exclusive_run_lock_support import (
    build_bash_program_that_acquires_then_sleeps,
    build_lock_file_path_for,
    run_bash_acquire_then_exit,
    stop_process_group,
    wait_until_lock_metadata_written,
)


def test_acquires_lock_and_releases_on_exit_without_replacing_the_lock_file(
    unique_lock_name_with_cleanup,
):
    completed = run_bash_acquire_then_exit(unique_lock_name_with_cleanup)
    assert completed.returncode == 0, completed.stderr
    lock_path = build_lock_file_path_for(unique_lock_name_with_cleanup)
    lock_inode = lock_path.stat().st_ino
    completed = run_bash_acquire_then_exit(unique_lock_name_with_cleanup)
    assert completed.returncode == 0, completed.stderr
    assert lock_path.stat().st_ino == lock_inode


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
        start_new_session=True,
    ) as holder:
        try:
            wait_until_lock_metadata_written(unique_lock_name_with_cleanup)
            completed = run_bash_acquire_then_exit(unique_lock_name_with_cleanup)
            assert completed.returncode == 99
            assert "LOCKED_BY_CONCURRENT_RUN" in completed.stderr
            assert "ScheduleWakeup(delaySeconds=" in completed.stderr
            assert unique_lock_name_with_cleanup in completed.stderr
            assert "started_at:           unknown" not in completed.stderr
        finally:
            stop_process_group(holder)


def test_stale_metadata_does_not_prevent_acquisition(unique_lock_name_with_cleanup):
    lock_path = build_lock_file_path_for(unique_lock_name_with_cleanup)
    lock_path.write_text(
        "pid=99999999\nstarted_epoch=1\nscript=stale\ntypical_duration_seconds=60\nlog_path=\n"
    )
    lock_inode = lock_path.stat().st_ino
    completed = run_bash_acquire_then_exit(unique_lock_name_with_cleanup)
    assert completed.returncode == 0, completed.stderr
    assert lock_path.stat().st_ino == lock_inode


def test_bypass_environment_variable_does_not_disable_exclusion(
    unique_lock_name_with_cleanup,
):
    holder_program = build_bash_program_that_acquires_then_sleeps(
        unique_lock_name_with_cleanup, sleep_seconds=5
    )
    with subprocess.Popen(
        ["bash", "-c", holder_program],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    ) as holder:
        try:
            wait_until_lock_metadata_written(unique_lock_name_with_cleanup)
            completed = run_bash_acquire_then_exit(
                unique_lock_name_with_cleanup,
                extra_env={"DOTFILES_BYPASS_EXCLUSIVE_RUN_LOCK": "1"},
            )
            assert completed.returncode == 99, completed.stderr
        finally:
            stop_process_group(holder)
