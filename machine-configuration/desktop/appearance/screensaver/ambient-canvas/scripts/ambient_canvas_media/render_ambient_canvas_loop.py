import argparse
import os
import signal
import sys

from ambient_canvas_browser import (
    resolve_chromium_browser_application,
)
from ambient_canvas_theme import RECORDING_BACKGROUND_COLOR_HEX
from recording.recorded_loop_capture_plan import (
    DEFAULT_CAPTURE_DURATION_SECONDS,
    DEFAULT_CAPTURE_FRAMES_PER_SECOND,
    RecordingConfiguration,
)
from recording.recorded_loop_capture_target import (
    compose_recorded_source_identifier,
    resolve_recorded_loop_capture_target,
)
from recording.recorded_loop_commit import commit_recorded_segment_manifest
from recording.recorded_loop_capture_pool import capture_recorded_playlist
from recording.recorded_loop_retention import discard_rendering_leftovers
from scene_video_cache import download_missing_scene_videos


def render_recorded_loop(
    index_file_path,
    capture_target,
    source_identifier,
    duration_seconds,
    frames_per_second,
):
    browser_application = resolve_chromium_browser_application()
    if browser_application is None:
        print(
            "render-ambient-canvas-loop: no Chromium browser installed", file=sys.stderr
        )
        return None

    os.makedirs(capture_target.loop_directory, exist_ok=True)
    download_missing_scene_videos(
        os.path.dirname(index_file_path), capture_target.scene_video_directory
    )
    uploaded_manifest_bytes = capture_recorded_playlist(
        index_file_path,
        capture_target,
        browser_application,
        RecordingConfiguration(
            duration_seconds, frames_per_second, RECORDING_BACKGROUND_COLOR_HEX
        ),
    )
    return commit_recorded_segment_manifest(
        capture_target.loop_directory,
        uploaded_manifest_bytes,
        source_identifier,
    )


def resolve_index_file_path():
    index_file_path = os.environ.get("AMBIENT_CANVAS_INDEX")
    if not index_file_path or not os.path.isfile(index_file_path):
        return None
    return index_file_path


def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("--output-directory", required=True)
    argument_parser.add_argument("--source-identifier", required=True)
    argument_parser.add_argument(
        "--seconds", type=int, default=DEFAULT_CAPTURE_DURATION_SECONDS
    )
    argument_parser.add_argument(
        "--fps", type=int, default=DEFAULT_CAPTURE_FRAMES_PER_SECOND
    )
    parsed_arguments = argument_parser.parse_args()

    index_file_path = resolve_index_file_path()
    if index_file_path is None:
        print("render-ambient-canvas-loop: web assets not found", file=sys.stderr)
        return 1

    capture_target = resolve_recorded_loop_capture_target(
        parsed_arguments.output_directory
    )
    manifest_path = render_recorded_loop(
        index_file_path,
        capture_target,
        compose_recorded_source_identifier(
            parsed_arguments.source_identifier, capture_target.capture_signature
        ),
        parsed_arguments.seconds,
        parsed_arguments.fps,
    )
    if manifest_path is None:
        return 1
    discard_rendering_leftovers(capture_target, parsed_arguments.source_identifier)
    print(manifest_path)
    return 0


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *ignored: sys.exit(1))
    sys.exit(main())
