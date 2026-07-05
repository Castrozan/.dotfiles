from __future__ import annotations

import psutil

from kill_runaway_chrome_devtools_mcp_instances import (
    find_chrome_devtools_mcp_processes,
    terminate_process_gracefully,
)

REPARENTED_ORPHAN_PARENT_NAMES = {"systemd", "init", "launchd"}
SIGTERM_GRACE_SECONDS = 5.0


def is_orphaned_by_parent(parent_pid, parent_name):
    if parent_pid is None:
        return True
    if parent_pid == 1:
        return True
    return parent_name in REPARENTED_ORPHAN_PARENT_NAMES


def read_parent_identity(process):
    try:
        parent = process.parent()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None, ""
    if parent is None:
        return None, ""
    try:
        return parent.pid, parent.name()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return parent.pid, ""


def find_orphaned_chrome_devtools_mcp_processes():
    orphaned_processes = []
    for process in find_chrome_devtools_mcp_processes():
        parent_pid, parent_name = read_parent_identity(process)
        if is_orphaned_by_parent(parent_pid, parent_name):
            orphaned_processes.append(process)
    return orphaned_processes


def log_watchdog_event(message):
    print(f"[chrome-devtools-mcp-orphan-reaper] {message}", flush=True)


def reap_orphaned_chrome_devtools_mcp_instances(sigterm_grace_seconds):
    for process in find_orphaned_chrome_devtools_mcp_processes():
        log_watchdog_event(
            f"reaping orphaned pid={process.pid}; spawning client is gone (reparented)"
        )
        terminate_process_gracefully(process, sigterm_grace_seconds)


def main():
    reap_orphaned_chrome_devtools_mcp_instances(SIGTERM_GRACE_SECONDS)


if __name__ == "__main__":
    main()
