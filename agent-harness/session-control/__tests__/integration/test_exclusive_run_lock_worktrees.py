import shutil
import subprocess

from exclusive_run_lock_support import (
    EXCLUSIVE_RUN_LOCK_HELPER_PATH,
    stop_process_group,
    wait_until_path_exists,
)


def test_worktree_helpers_compete_for_the_same_lock(
    unique_lock_name_with_cleanup, tmp_path
):
    lock_name = unique_lock_name_with_cleanup
    start = tmp_path / "start"
    release = tmp_path / "release"
    holders = []
    results = []
    try:
        for index in range(3):
            worktree = tmp_path / f"worktree-{index}"
            worktree.mkdir()
            for source in (
                EXCLUSIVE_RUN_LOCK_HELPER_PATH,
                EXCLUSIVE_RUN_LOCK_HELPER_PATH.with_name("exclusive_run_lock.py"),
                EXCLUSIVE_RUN_LOCK_HELPER_PATH.with_name("exclusive_run_owner.py"),
                EXCLUSIVE_RUN_LOCK_HELPER_PATH.with_name(
                    "exclusive_run_diagnostics.py"
                ),
            ):
                shutil.copyfile(source, worktree / source.name)
            shutil.copytree(
                EXCLUSIVE_RUN_LOCK_HELPER_PATH.parent / "agent_session",
                worktree / "agent_session",
            )
            result = worktree / "result"
            results.append(result)
            program = f'''while [[ ! -f "{start}" ]]; do sleep 0.01; done
(
    source "{worktree}/exclusive-run-lock.sh"
    acquire_exclusive_run_lock_or_emit_retry_instructions "{lock_name}" 60
    echo 0 > "{result}"
    while [[ ! -f "{release}" ]]; do sleep 0.01; done
)
status=$?
if [[ "$status" -ne 0 ]]; then echo "$status" > "{result}"; fi
'''
            holders.append(
                subprocess.Popen(
                    ["bash", "-c", program],
                    stderr=subprocess.PIPE,
                    start_new_session=True,
                )
            )
        start.touch()
        for result in results:
            wait_until_path_exists(result)
        assert sorted(int(result.read_text()) for result in results) == [0, 99, 99]
        release.touch()
        for holder in holders:
            holder.communicate(timeout=5)
            assert holder.returncode == 0
    finally:
        for holder in holders:
            stop_process_group(holder)
