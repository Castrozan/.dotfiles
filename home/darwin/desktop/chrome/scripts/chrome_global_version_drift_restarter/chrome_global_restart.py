from __future__ import annotations

import subprocess
import time

import psutil
from chrome_global_processes import (
    find_chrome_global_processes,
    process_is_chrome_child,
)
from restarter_log import log_event

GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS = 10.0
SHUTDOWN_POLL_INTERVAL_SECONDS = 0.5
RELAUNCH_TIMEOUT_SECONDS = 30.0


def terminate_chrome_global_main_processes_gracefully(timeout_seconds: float) -> bool:
    for process in find_chrome_global_processes():
        if process_is_chrome_child(process):
            continue
        try:
            process.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    shutdown_deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < shutdown_deadline:
        if not find_chrome_global_processes():
            return True
        time.sleep(SHUTDOWN_POLL_INTERVAL_SECONDS)
    return not find_chrome_global_processes()


def force_kill_remaining_chrome_global_processes() -> None:
    for process in find_chrome_global_processes():
        try:
            process.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue


def relaunch_chrome_global_via_launcher(launcher_binary_path: str) -> None:
    try:
        subprocess.run(
            [launcher_binary_path],
            timeout=RELAUNCH_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as relaunch_error:
        log_event(f"relaunch via {launcher_binary_path} failed: {relaunch_error}")


def restart_chrome_global(
    launcher_binary_path: str,
    on_disk_version: str,
    running_framework_versions: set[str],
) -> bool:
    log_event(
        f"restarting chrome-global: on-disk={on_disk_version} "
        f"running={sorted(running_framework_versions)}"
    )
    shut_down_cleanly = terminate_chrome_global_main_processes_gracefully(
        GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS
    )
    if not shut_down_cleanly:
        log_event("graceful shutdown timed out; force-killing remaining processes")
        force_kill_remaining_chrome_global_processes()
        time.sleep(SHUTDOWN_POLL_INTERVAL_SECONDS)
    if find_chrome_global_processes():
        log_event(
            "chrome-global processes survived teardown; skipping relaunch so the "
            "next cycle retries instead of focusing the stale instance"
        )
        return False
    relaunch_chrome_global_via_launcher(launcher_binary_path)
    return True
