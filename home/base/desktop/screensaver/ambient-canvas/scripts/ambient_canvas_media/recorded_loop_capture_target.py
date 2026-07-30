import os
from collections import namedtuple

from ambient_canvas_browser import read_screen_dimensions
from recorded_loop_capture_plan import (
    format_capture_signature,
    resolve_capture_pixel_dimensions,
)
from recorded_segment_store import resolve_recorded_loop_directory
from scene_video_cache import resolve_scene_video_directory

PLAYBACK_DWELL_OVERRIDE_FILENAME = "playback-dwell-seconds"

RecordedLoopCaptureTarget = namedtuple(
    "RecordedLoopCaptureTarget",
    (
        "loop_directory",
        "scene_video_directory",
        "playback_dwell_override_path",
        "screen_dimensions",
        "capture_pixel_dimensions",
        "capture_signature",
    ),
)


def resolve_playback_dwell_override_path(state_directory):
    return os.path.join(state_directory, PLAYBACK_DWELL_OVERRIDE_FILENAME)


def compose_recorded_source_identifier(source_identifier, capture_signature):
    return f"{source_identifier} capture={capture_signature}"


def resolve_recorded_loop_capture_target(state_directory):
    screen_dimensions = read_screen_dimensions()
    capture_pixel_dimensions = resolve_capture_pixel_dimensions(*screen_dimensions)
    capture_signature = format_capture_signature(capture_pixel_dimensions)
    return RecordedLoopCaptureTarget(
        loop_directory=resolve_recorded_loop_directory(
            state_directory, capture_signature
        ),
        scene_video_directory=resolve_scene_video_directory(state_directory),
        playback_dwell_override_path=resolve_playback_dwell_override_path(
            state_directory
        ),
        screen_dimensions=screen_dimensions,
        capture_pixel_dimensions=capture_pixel_dimensions,
        capture_signature=capture_signature,
    )
