import argparse
import os
import subprocess
import sys

DEFAULT_PLAYER_BINARY_PATH = os.path.expanduser("~/.local/bin/ambient-canvas-player")


def resolve_recorded_loop_media_path(output_directory):
    pointer_path = os.path.join(output_directory, "loop.current")
    if not os.path.isfile(pointer_path):
        return None
    with open(pointer_path) as pointer_file:
        media_filename = pointer_file.read().strip()
    if not media_filename:
        return None
    media_path = os.path.join(output_directory, media_filename)
    if not os.path.isfile(media_path):
        return None
    return media_path


def build_player_process_arguments(player_binary_path, recorded_loop_media_path):
    return [player_binary_path, recorded_loop_media_path]


def launch_display(player_binary_path, output_directory):
    if not os.path.isfile(player_binary_path):
        print(
            "display-ambient-canvas-loop: native player binary not built",
            file=sys.stderr,
        )
        return 1
    recorded_loop_media_path = resolve_recorded_loop_media_path(output_directory)
    if recorded_loop_media_path is None:
        print("display-ambient-canvas-loop: no recorded loop to play", file=sys.stderr)
        return 1
    subprocess.Popen(
        build_player_process_arguments(player_binary_path, recorded_loop_media_path),
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
