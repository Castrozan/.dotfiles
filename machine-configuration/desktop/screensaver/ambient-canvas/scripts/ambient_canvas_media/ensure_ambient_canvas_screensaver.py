import argparse
import os
import shutil
import signal
import subprocess
import sys
import time

from display_ambient_canvas_loop import (
    DEFAULT_PLAYER_BINARY_PATH,
    launch_display,
)
from recorded_loop_capture_plan import (
    DEFAULT_CAPTURE_DURATION_SECONDS,
    DEFAULT_CAPTURE_FRAMES_PER_SECOND,
)
from recorded_loop_capture_target import (
    compose_recorded_source_identifier,
    resolve_recorded_loop_capture_target,
)
from recorded_segment_store import (
    read_recorded_source_identifier,
    resolve_playable_segment_manifest_path,
    resolve_recorded_segment_manifest_path,
)
from render_ambient_canvas_loop import (
    render_recorded_loop,
    resolve_index_file_path,
)


def recorded_loop_exists(loop_directory):
    return resolve_playable_segment_manifest_path(loop_directory) is not None


def recorded_loop_is_fresh(loop_directory, source_identifier):
    return read_recorded_source_identifier(
        loop_directory
    ) == source_identifier and recorded_loop_exists(loop_directory)


def resolve_display_process_name(player_binary_path):
    return os.path.basename(player_binary_path)


def resolve_loop_display_process_marker(player_binary_path, loop_directory):
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


def is_display_running_for_loop(player_binary_path, loop_directory):
    return a_process_matches(
        ["-f", resolve_loop_display_process_marker(player_binary_path, loop_directory)]
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


def ensure_screensaver(
    index_file_path,
    capture_target,
    source_identifier,
    player_binary_path,
    duration_seconds,
    frames_per_second,
):
    loop_directory = capture_target.loop_directory
    recorded_loop_was_replaced = False
    if not recorded_loop_is_fresh(loop_directory, source_identifier):
        rendered_manifest_path = render_recorded_loop(
            index_file_path,
            capture_target,
            source_identifier,
            duration_seconds,
            frames_per_second,
        )
        if rendered_manifest_path is None and not recorded_loop_exists(loop_directory):
            return 1
        recorded_loop_was_replaced = rendered_manifest_path is not None

    if not recorded_loop_was_replaced and is_display_running_for_loop(
        player_binary_path, loop_directory
    ):
        return 0
    stop_every_display(player_binary_path)
    wait_for_every_display_to_exit(player_binary_path)
    return launch_display(
        player_binary_path, loop_directory, capture_target.playback_dwell_override_path
    )


def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("--output-directory", required=True)
    argument_parser.add_argument("--source-identifier", required=True)
    argument_parser.add_argument("--player-binary", default=DEFAULT_PLAYER_BINARY_PATH)
    argument_parser.add_argument(
        "--seconds", type=int, default=DEFAULT_CAPTURE_DURATION_SECONDS
    )
    argument_parser.add_argument(
        "--fps", type=int, default=DEFAULT_CAPTURE_FRAMES_PER_SECOND
    )
    parsed_arguments = argument_parser.parse_args()

    index_file_path = resolve_index_file_path()
    if index_file_path is None:
        print(
            "ensure-ambient-canvas-screensaver: web assets not found", file=sys.stderr
        )
        return 1

    capture_target = resolve_recorded_loop_capture_target(
        parsed_arguments.output_directory
    )
    return ensure_screensaver(
        index_file_path,
        capture_target,
        compose_recorded_source_identifier(
            parsed_arguments.source_identifier, capture_target.capture_signature
        ),
        parsed_arguments.player_binary,
        parsed_arguments.seconds,
        parsed_arguments.fps,
    )


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *ignored: sys.exit(1))
    sys.exit(main())
