import os
import subprocess

from exclusive_run_lock_support import (
    build_bash_program_that_acquires_then_sleeps,
    run_bash_acquire_then_exit,
    stop_process_group,
    wait_until_lock_metadata_written,
)


def test_contention_identifies_the_active_agent_and_does_not_schedule_a_retry(
    unique_lock_name_with_cleanup,
):
    program = build_bash_program_that_acquires_then_sleeps(
        unique_lock_name_with_cleanup, sleep_seconds=30
    )
    holder = subprocess.Popen(
        ["bash", "-c", program],
        env={
            **os.environ,
            "CLAWDE_AGENT_NAME": "fixture-owner",
            "CODEX_THREAD_ID": "fixture-owner-session",
            "HERDR_PANE_ID": "fixture-owner-pane",
        },
        start_new_session=True,
    )
    try:
        wait_until_lock_metadata_written(unique_lock_name_with_cleanup)
        completed = run_bash_acquire_then_exit(
            unique_lock_name_with_cleanup,
            extra_env={"CLAWDE_AGENT_NAME": "fixture-contender"},
        )
        assert completed.returncode == 99
        assert "owner_type:           agent" in completed.stderr
        assert "agent_name:           fixture-owner" in completed.stderr
        assert "agent_harness:        codex" in completed.stderr
        assert "agent_session:        fixture-owner-session" in completed.stderr
        assert "herdr_pane:           fixture-owner-pane" in completed.stderr
        assert "fixture-contender" not in completed.stderr
        assert "nothing was queued" in completed.stderr
        assert "intentionally" in completed.stderr
        assert "ScheduleWakeup" not in completed.stderr
    finally:
        stop_process_group(holder)
