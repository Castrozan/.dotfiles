from __future__ import annotations

import json
import time
from pathlib import Path

import psutil

CHROME_DEVTOOLS_MCP_PROCESS_MATCH_TOKEN = "chrome-devtools-mcp"
CPU_PERCENT_RUNAWAY_THRESHOLD = 130.0
CPU_SAMPLE_INTERVAL_SECONDS = 3.0
CONSECUTIVE_STRIKES_BEFORE_TERMINATION = 4
SIGTERM_GRACE_SECONDS = 5.0
STRIKE_STATE_FILE_PATH = Path("/tmp/chrome-devtools-mcp-runaway-watchdog-strikes.json")


def build_stable_process_key(process) -> str:
    return f"{process.pid}:{int(process.create_time())}"


def find_chrome_devtools_mcp_processes():
    matched_processes = []
    for process in psutil.process_iter(["pid", "name", "cmdline", "create_time"]):
        try:
            joined_command_line = " ".join(process.info["cmdline"] or [])
            process_name = process.info["name"] or ""
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        if (
            CHROME_DEVTOOLS_MCP_PROCESS_MATCH_TOKEN in joined_command_line
            or CHROME_DEVTOOLS_MCP_PROCESS_MATCH_TOKEN in process_name
        ):
            matched_processes.append(process)
    return matched_processes


def measure_cpu_percent_per_process(processes, sample_interval_seconds):
    for process in processes:
        try:
            process.cpu_percent(None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    time.sleep(sample_interval_seconds)
    cpu_percent_by_process_key = {}
    for process in processes:
        try:
            cpu_percent_by_process_key[build_stable_process_key(process)] = (
                process.cpu_percent(None)
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return cpu_percent_by_process_key


def compute_updated_strike_counts(
    previous_strike_counts, cpu_percent_by_process_key, runaway_threshold
):
    updated_strike_counts = {}
    for process_key, cpu_percent in cpu_percent_by_process_key.items():
        if cpu_percent >= runaway_threshold:
            updated_strike_counts[process_key] = (
                previous_strike_counts.get(process_key, 0) + 1
            )
        else:
            updated_strike_counts[process_key] = 0
    return updated_strike_counts


def select_process_keys_to_terminate(
    strike_counts, consecutive_strikes_before_termination
):
    return [
        process_key
        for process_key, strike_count in strike_counts.items()
        if strike_count >= consecutive_strikes_before_termination
    ]


def read_persisted_strike_counts(state_file_path):
    try:
        return json.loads(state_file_path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def write_persisted_strike_counts(state_file_path, strike_counts):
    state_file_path.write_text(json.dumps(strike_counts))


def terminate_process_gracefully(process, sigterm_grace_seconds):
    try:
        process.terminate()
        process.wait(timeout=sigterm_grace_seconds)
    except psutil.TimeoutExpired:
        try:
            process.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return


def log_watchdog_event(message):
    print(f"[chrome-devtools-mcp-runaway-watchdog] {message}", flush=True)


def main():
    live_processes = find_chrome_devtools_mcp_processes()
    if not live_processes:
        write_persisted_strike_counts(STRIKE_STATE_FILE_PATH, {})
        return

    cpu_percent_by_process_key = measure_cpu_percent_per_process(
        live_processes, CPU_SAMPLE_INTERVAL_SECONDS
    )
    previous_strike_counts = read_persisted_strike_counts(STRIKE_STATE_FILE_PATH)
    updated_strike_counts = compute_updated_strike_counts(
        previous_strike_counts,
        cpu_percent_by_process_key,
        CPU_PERCENT_RUNAWAY_THRESHOLD,
    )

    process_by_key = {
        build_stable_process_key(process): process for process in live_processes
    }
    for process_key in select_process_keys_to_terminate(
        updated_strike_counts, CONSECUTIVE_STRIKES_BEFORE_TERMINATION
    ):
        process = process_by_key.get(process_key)
        if process is None:
            continue
        log_watchdog_event(
            f"terminating runaway pid={process.pid} "
            f"cpu={cpu_percent_by_process_key.get(process_key, 0.0):.0f}% "
            f"after {updated_strike_counts[process_key]} consecutive strikes "
            f"over {CPU_PERCENT_RUNAWAY_THRESHOLD:.0f}%"
        )
        terminate_process_gracefully(process, SIGTERM_GRACE_SECONDS)
        updated_strike_counts[process_key] = 0

    write_persisted_strike_counts(STRIKE_STATE_FILE_PATH, updated_strike_counts)


if __name__ == "__main__":
    main()
