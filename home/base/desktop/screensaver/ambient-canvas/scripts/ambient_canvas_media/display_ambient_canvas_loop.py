import argparse
import os
import subprocess
import sys

from recorded_loop_capture_target import resolve_recorded_loop_capture_target
from recorded_segment_store import resolve_playable_segment_manifest_path

DEFAULT_PLAYER_BINARY_PATH = os.path.expanduser("~/.local/bin/ᓚᘏᗢ")


def build_player_process_arguments(
    player_binary_path, segment_manifest_path, playback_dwell_override_path
):
    return [player_binary_path, segment_manifest_path, playback_dwell_override_path]


def launch_display(player_binary_path, loop_directory, playback_dwell_override_path):
    if not os.path.isfile(player_binary_path):
        print(
            "display-ambient-canvas-loop: native player binary not built",
            file=sys.stderr,
        )
        return 1
    segment_manifest_path = resolve_playable_segment_manifest_path(loop_directory)
    if segment_manifest_path is None:
        print("display-ambient-canvas-loop: no recorded loop to play", file=sys.stderr)
        return 1
    subprocess.Popen(
        build_player_process_arguments(
            player_binary_path, segment_manifest_path, playback_dwell_override_path
        ),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return 0


def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("--output-directory", required=True)
    argument_parser.add_argument("--player-binary", default=DEFAULT_PLAYER_BINARY_PATH)
    parsed_arguments = argument_parser.parse_args()
    capture_target = resolve_recorded_loop_capture_target(
        parsed_arguments.output_directory
    )
    return launch_display(
        parsed_arguments.player_binary,
        capture_target.loop_directory,
        capture_target.playback_dwell_override_path,
    )


if __name__ == "__main__":
    sys.exit(main())
