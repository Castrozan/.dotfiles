import os
import signal
import subprocess
import time

WATCHDOG_POLL_INTERVAL_SECONDS = 30
WATCHDOG_CONSECUTIVE_STUCK_THRESHOLD = 2
PANE_CAPTURE_LINE_COUNT = 80
USAGE_LIMIT_MODAL_INDICATORS = [
    "Wait for limit to reset",
    "Adjust monthly spend limit",
    "You've hit your weekly limit",
]


def pane_indicates_usage_limit_modal(pane_content: str) -> bool:
    return any(indicator in pane_content for indicator in USAGE_LIMIT_MODAL_INDICATORS)


def capture_pane_content(tmux_target: str) -> str | None:
    result = subprocess.run(
        [
            "tmux",
            "capture-pane",
            "-p",
            "-t",
            tmux_target,
            "-S",
            f"-{PANE_CAPTURE_LINE_COUNT}",
        ],
        capture_output=True,
        text=True,
    )
    return result.stdout if result.returncode == 0 else None


def collect_descendant_process_ids(parent_process_id: int) -> list[int]:
    result = subprocess.run(
        ["pgrep", "-P", str(parent_process_id)],
        capture_output=True,
        text=True,
    )
    descendant_process_ids: list[int] = []
    for line in result.stdout.split():
        child_process_id = int(line)
        descendant_process_ids.extend(collect_descendant_process_ids(child_process_id))
        descendant_process_ids.append(child_process_id)
    return descendant_process_ids


def terminate_process_tree(root_process_id: int) -> None:
    for process_id in collect_descendant_process_ids(root_process_id) + [
        root_process_id
    ]:
        try:
            os.kill(process_id, signal.SIGTERM)
        except ProcessLookupError:
            pass


def run_launch_command_once(
    launch_command: str,
    heartbeat_driver_argv: list[str] | None,
    tmux_target: str | None,
) -> tuple[float, bool]:
    start_time = time.time()
    agent_process = subprocess.Popen(["bash", "-c", launch_command])
    driver_process = (
        subprocess.Popen(heartbeat_driver_argv) if heartbeat_driver_argv else None
    )
    consecutive_stuck_polls = 0
    was_stuck_kill = False
    try:
        while True:
            try:
                agent_process.wait(timeout=WATCHDOG_POLL_INTERVAL_SECONDS)
                break
            except subprocess.TimeoutExpired:
                if tmux_target is None:
                    continue
                pane_content = capture_pane_content(tmux_target)
                if pane_content is not None and pane_indicates_usage_limit_modal(
                    pane_content
                ):
                    consecutive_stuck_polls += 1
                else:
                    consecutive_stuck_polls = 0
                if consecutive_stuck_polls >= WATCHDOG_CONSECUTIVE_STUCK_THRESHOLD:
                    print(
                        f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                        "Usage-limit modal detected in pane. "
                        "Terminating session to trigger a restart.",
                        flush=True,
                    )
                    terminate_process_tree(agent_process.pid)
                    agent_process.wait()
                    was_stuck_kill = True
                    break
    finally:
        if driver_process is not None:
            driver_process.terminate()
            try:
                driver_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                driver_process.kill()
    return time.time() - start_time, was_stuck_kill
