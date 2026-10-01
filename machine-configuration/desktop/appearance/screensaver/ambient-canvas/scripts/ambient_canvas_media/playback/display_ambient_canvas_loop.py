import argparse
import logging
import os
from pathlib import Path
import subprocess
import sys

from playback.player_diagnostics import create_player_run
from recording.recorded_loop_capture_target import resolve_recorded_loop_capture_target
from recording.recorded_segment_store import resolve_playable_segment_manifest_path

DEFAULT_PLAYER_BINARY_PATH = os.path.expanduser("~/.local/bin/ᓚᘏᗢ")


def build_player_process_arguments(
    player_binary_path, segment_manifest_path, playback_dwell_override_path
):
    return [player_binary_path, segment_manifest_path, playback_dwell_override_path]


def launch_display(player_binary_path, loop_directory, playback_dwell_override_path):
    if not os.path.isfile(player_binary_path):
        logging.getLogger("ambient_canvas.launcher").error(
            "player_binary_missing path=%s", player_binary_path
        )
        print(
            "display-ambient-canvas-loop: native player binary not built",
            file=sys.stderr,
        )
        return 1
    segment_manifest_path = resolve_playable_segment_manifest_path(loop_directory)
    if segment_manifest_path is None:
        logging.getLogger("ambient_canvas.launcher").error(
            "playable_loop_missing directory=%s", loop_directory
        )
        print("display-ambient-canvas-loop: no recorded loop to play", file=sys.stderr)
        return 1
    run_directory = create_player_run(Path(playback_dwell_override_path).parent)
    supervisor_path = Path(__file__).with_name("supervise_ambient_canvas_player.py")
    with (run_directory / "supervisor.log").open("ab") as supervisor_log:
        supervisor_process = subprocess.Popen(
            [
                sys.executable,
                str(supervisor_path),
                str(run_directory),
                *build_player_process_arguments(
                    player_binary_path,
                    segment_manifest_path,
                    playback_dwell_override_path,
                ),
            ],
            stdin=subprocess.DEVNULL,
            stdout=supervisor_log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    logging.getLogger("ambient_canvas.launcher").info(
        "player_supervisor_started pid=%s report=%s",
        supervisor_process.pid,
        run_directory / "report.json",
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
