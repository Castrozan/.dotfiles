import argparse
import os
import signal
import subprocess
import sys
import time

from display_ambient_canvas_loop import (
    DEFAULT_DISPLAY_PROFILE_DIRECTORY,
    launch_display,
)
from render_ambient_canvas_loop import (
    DEFAULT_CAPTURE_DURATION_SECONDS,
    DEFAULT_CAPTURE_FRAMES_PER_SECOND,
    render_recorded_loop,
    resolve_index_file_path,
)


def recorded_loop_is_fresh(output_directory, source_identifier):
    source_path = os.path.join(output_directory, "loop.source")
    pointer_path = os.path.join(output_directory, "loop.current")
    if not os.path.isfile(source_path) or not os.path.isfile(pointer_path):
        return False
    with open(source_path) as source_file:
        recorded_source_identifier = source_file.read().strip()
    if recorded_source_identifier != source_identifier:
        return False
    with open(pointer_path) as pointer_file:
        media_filename = pointer_file.read().strip()
    return bool(media_filename) and os.path.isfile(
        os.path.join(output_directory, media_filename)
    )


def recorded_loop_exists(output_directory):
    pointer_path = os.path.join(output_directory, "loop.current")
    if not os.path.isfile(pointer_path):
        return False
    with open(pointer_path) as pointer_file:
        media_filename = pointer_file.read().strip()
    return bool(media_filename) and os.path.isfile(
        os.path.join(output_directory, media_filename)
    )


def is_display_running(display_profile_directory):
    completed = subprocess.run(
        ["/usr/bin/pgrep", "-f", display_profile_directory],
        check=False,
        capture_output=True,
    )
    return completed.returncode == 0


def stop_display(display_profile_directory):
    subprocess.run(
        ["/usr/bin/pkill", "-f", display_profile_directory],
        check=False,
        capture_output=True,
    )


def wait_for_display_to_exit(
    display_profile_directory, timeout_seconds=5.0, poll_interval_seconds=0.2
):
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not is_display_running(display_profile_directory):
            return
        time.sleep(poll_interval_seconds)


def ensure_screensaver(
    index_file_path,
    output_directory,
    source_identifier,
    display_profile_directory,
    duration_seconds,
    frames_per_second,
):
    display_needs_relaunch = False
    if not recorded_loop_is_fresh(output_directory, source_identifier):
        rendered_media_filename = render_recorded_loop(
            index_file_path,
            output_directory,
            source_identifier,
            duration_seconds,
            frames_per_second,
        )
        if rendered_media_filename is None and not recorded_loop_exists(
            output_directory
        ):
            return 1
        if rendered_media_filename is not None and is_display_running(
            display_profile_directory
        ):
            stop_display(display_profile_directory)
            wait_for_display_to_exit(display_profile_directory)
            display_needs_relaunch = True

    if display_needs_relaunch or not is_display_running(display_profile_directory):
        return launch_display(
            index_file_path, output_directory, display_profile_directory
        )
    return 0


def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("--output-directory", required=True)
    argument_parser.add_argument("--source-identifier", required=True)
    argument_parser.add_argument(
        "--profile-directory", default=DEFAULT_DISPLAY_PROFILE_DIRECTORY
    )
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

    return ensure_screensaver(
        index_file_path,
        parsed_arguments.output_directory,
        parsed_arguments.source_identifier,
        parsed_arguments.profile_directory,
        parsed_arguments.seconds,
        parsed_arguments.fps,
    )


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *ignored: sys.exit(1))
    sys.exit(main())
