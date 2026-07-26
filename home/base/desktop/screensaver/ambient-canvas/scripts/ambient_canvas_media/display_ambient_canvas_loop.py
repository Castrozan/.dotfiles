import argparse
import os
import subprocess
import sys

from recorded_segment_store import resolve_playable_segment_manifest_path

DEFAULT_PLAYER_BINARY_PATH = os.path.expanduser("~/.local/bin/ᓚᘏᗢ")


def build_player_process_arguments(player_binary_path, segment_manifest_path):
    return [player_binary_path, segment_manifest_path]


def launch_display(player_binary_path, output_directory):
    if not os.path.isfile(player_binary_path):
        print(
            "display-ambient-canvas-loop: native player binary not built",
            file=sys.stderr,
        )
        return 1
    segment_manifest_path = resolve_playable_segment_manifest_path(output_directory)
    if segment_manifest_path is None:
        print("display-ambient-canvas-loop: no recorded loop to play", file=sys.stderr)
        return 1
    subprocess.Popen(
        build_player_process_arguments(player_binary_path, segment_manifest_path),
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
    return launch_display(
        parsed_arguments.player_binary, parsed_arguments.output_directory
    )


if __name__ == "__main__":
    sys.exit(main())
