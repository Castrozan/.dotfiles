import argparse
import ctypes
import signal
import sys

from mpv_ambient_canvas_player import run_player

PLAYER_PROCESS_NAME = "ᓚᘏᗢ"
PROCESS_NAME_SET_PRCTL_OPTION = 15


def set_process_name(process_name):
    process_name_bytes = process_name.encode("utf-8")[:15]
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    libc.prctl(PROCESS_NAME_SET_PRCTL_OPTION, process_name_bytes, 0, 0, 0)


def parse_player_arguments(arguments):
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("segment_manifest_path")
    argument_parser.add_argument("playback_dwell_override_path")
    parsed_arguments = argument_parser.parse_args(arguments)
    return (
        parsed_arguments.segment_manifest_path,
        parsed_arguments.playback_dwell_override_path,
    )


def main():
    set_process_name(PLAYER_PROCESS_NAME)
    segment_manifest_path, playback_dwell_override_path = parse_player_arguments(
        sys.argv[1:]
    )
    signal.signal(signal.SIGTERM, lambda *ignored: sys.exit(1))
    return run_player(segment_manifest_path, playback_dwell_override_path)


if __name__ == "__main__":
    sys.exit(main())
