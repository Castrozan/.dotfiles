import argparse
import logging
import os
from pathlib import Path
import sys

from playback.player_diagnostics import create_player_run
from playback.player_processes import (
    stop_every_display,
    wait_for_every_display_to_exit,
)
from playback.supervise_ambient_canvas_player import supervise_player
from recording.recorded_loop_capture_target import resolve_recorded_loop_capture_target
from recording.recorded_segment_store import resolve_playable_segment_manifest_path

DEFAULT_PLAYER_BINARY_PATH = os.path.expanduser("~/.local/bin/ᓚᘏᗢ")
LAUNCHER_LOGGER_NAME = "ambient_canvas.launcher"


def build_player_process_arguments(
    player_binary_path, segment_manifest_path, playback_dwell_override_path
):
    return [player_binary_path, segment_manifest_path, playback_dwell_override_path]


def play_recorded_loop(
    player_binary_path, loop_directory, playback_dwell_override_path
):
    if not os.path.isfile(player_binary_path):
        logging.getLogger(LAUNCHER_LOGGER_NAME).error(
            "player_binary_missing path=%s", player_binary_path
        )
        print(
            "display-ambient-canvas-loop: native player binary not built",
            file=sys.stderr,
        )
        return 1
    segment_manifest_path = resolve_playable_segment_manifest_path(loop_directory)
    if segment_manifest_path is None:
        logging.getLogger(LAUNCHER_LOGGER_NAME).error(
            "playable_loop_missing directory=%s", loop_directory
        )
        print("display-ambient-canvas-loop: no recorded loop to play", file=sys.stderr)
        return 1
    stop_every_display(player_binary_path)
    wait_for_every_display_to_exit(player_binary_path)
    run_directory = create_player_run(Path(playback_dwell_override_path).parent)
    return supervise_player(
        run_directory,
        build_player_process_arguments(
            player_binary_path, segment_manifest_path, playback_dwell_override_path
        ),
    )


def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("--output-directory", required=True)
    argument_parser.add_argument("--player-binary", default=DEFAULT_PLAYER_BINARY_PATH)
    parsed_arguments = argument_parser.parse_args()
    capture_target = resolve_recorded_loop_capture_target(
        parsed_arguments.output_directory
    )
    return play_recorded_loop(
        parsed_arguments.player_binary,
        capture_target.loop_directory,
        capture_target.playback_dwell_override_path,
    )


if __name__ == "__main__":
    sys.exit(main())
