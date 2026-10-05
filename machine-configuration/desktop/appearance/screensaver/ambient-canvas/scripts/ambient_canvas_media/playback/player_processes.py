import os
import shutil
import subprocess
import time

from recording.recorded_segment_store import resolve_recorded_segment_manifest_path


def resolve_display_process_name(player_binary_path):
    return os.path.basename(player_binary_path)


def resolve_loop_display_process_marker(loop_directory):
    return resolve_recorded_segment_manifest_path(loop_directory)


def resolve_process_tool(tool_name):
    return shutil.which(tool_name) or f"/usr/bin/{tool_name}"


def a_process_matches(match_arguments):
    completed = subprocess.run(
        [resolve_process_tool("pgrep"), *match_arguments],
        check=False,
        capture_output=True,
    )
    return completed.returncode == 0


def any_display_is_running(player_binary_path):
    return a_process_matches(["-x", resolve_display_process_name(player_binary_path)])


def is_display_running_for_loop(loop_directory):
    return a_process_matches(
        ["-f", resolve_loop_display_process_marker(loop_directory)]
    )


def stop_every_display(player_binary_path):
    subprocess.run(
        [
            resolve_process_tool("pkill"),
            "-x",
            resolve_display_process_name(player_binary_path),
        ],
        check=False,
        capture_output=True,
    )


def wait_for_every_display_to_exit(
    player_binary_path, timeout_seconds=5.0, poll_interval_seconds=0.2
):
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not any_display_is_running(player_binary_path):
            return
        time.sleep(poll_interval_seconds)


def a_record_pass_is_running():
    return a_process_matches(["-f", "ambient-canvas-record-"])
