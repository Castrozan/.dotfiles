import os
import re
import shutil

from playback.player_processes import a_record_pass_is_running
from recording.recorded_loop_capture_target import compose_recorded_source_identifier
from recording.recorded_segment_store import read_recorded_source_identifier

CAPTURE_SIGNATURE_PATTERN = re.compile(r"\d+x\d+\Z")


def recorded_loop_is_current(loop_directory, rendering_source_identifier):
    return read_recorded_source_identifier(
        loop_directory
    ) == compose_recorded_source_identifier(
        rendering_source_identifier, os.path.basename(loop_directory)
    )


def list_stale_sibling_loop_directories(loop_directory, rendering_source_identifier):
    loops_directory = os.path.dirname(loop_directory)
    if not os.path.isdir(loops_directory):
        return []
    return [
        sibling_directory
        for sibling_directory in (
            os.path.join(loops_directory, sibling_name)
            for sibling_name in sorted(os.listdir(loops_directory))
            if CAPTURE_SIGNATURE_PATTERN.match(sibling_name)
        )
        if os.path.isdir(sibling_directory)
        and os.path.abspath(sibling_directory) != os.path.abspath(loop_directory)
        and not recorded_loop_is_current(sibling_directory, rendering_source_identifier)
    ]


def discard_rendering_leftovers(capture_target, rendering_source_identifier):
    if a_record_pass_is_running():
        return []
    discarded_paths = list_stale_sibling_loop_directories(
        capture_target.loop_directory, rendering_source_identifier
    )
    if os.path.isdir(capture_target.scene_video_directory):
        discarded_paths.append(capture_target.scene_video_directory)
    for discarded_path in discarded_paths:
        shutil.rmtree(discarded_path, ignore_errors=True)
    return discarded_paths
