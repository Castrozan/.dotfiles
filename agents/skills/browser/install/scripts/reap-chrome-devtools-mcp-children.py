import os
import signal
import subprocess
import sys


def parse_elapsed_time_to_seconds(elapsed_time_text):
    remaining_text = elapsed_time_text
    days = 0
    if "-" in remaining_text:
        days_text, remaining_text = remaining_text.split("-", 1)
        days = int(days_text)
    time_components = [int(component) for component in remaining_text.split(":")]
    while len(time_components) < 3:
        time_components.insert(0, 0)
    hours, minutes, seconds = time_components
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def select_reapable_chrome_devtools_mcp_child_process_ids(
    process_status_output, own_process_id, minimum_age_seconds
):
    reapable_process_ids = []
    for process_status_line in process_status_output.splitlines():
        stripped_line = process_status_line.strip()
        if not stripped_line:
            continue
        process_id_text, remainder_after_process_id = stripped_line.split(maxsplit=1)
        elapsed_time_text, command_text = remainder_after_process_id.split(maxsplit=1)
        process_id = int(process_id_text)
        if process_id == own_process_id:
            continue
        if "bin/chrome-devtools-mcp" not in command_text:
            continue
        if "supergateway" in command_text:
            continue
        if parse_elapsed_time_to_seconds(elapsed_time_text) < minimum_age_seconds:
            continue
        reapable_process_ids.append(process_id)
    return reapable_process_ids


def collect_process_status_output():
    return subprocess.run(
        ["ps", "-Awwo", "pid=,etime=,command="],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def send_kill_signal_to_process_ids(process_ids):
    killed_process_ids = []
    for process_id in process_ids:
        try:
            os.kill(process_id, signal.SIGKILL)
            killed_process_ids.append(process_id)
        except ProcessLookupError:
            continue
    return killed_process_ids


def main():
    minimum_age_seconds = int(os.environ.get("MINIMUM_AGE_SECONDS", "0"))
    reapable_process_ids = select_reapable_chrome_devtools_mcp_child_process_ids(
        collect_process_status_output(), os.getpid(), minimum_age_seconds
    )
    killed_process_ids = send_kill_signal_to_process_ids(reapable_process_ids)
    if killed_process_ids:
        print(
            "reaped chrome-devtools-mcp children older than "
            f"{minimum_age_seconds}s: "
            + " ".join(str(process_id) for process_id in killed_process_ids)
        )


if __name__ == "__main__":
    sys.exit(main())
