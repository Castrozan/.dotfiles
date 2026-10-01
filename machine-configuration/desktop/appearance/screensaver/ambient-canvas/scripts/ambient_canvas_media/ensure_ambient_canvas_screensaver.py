import argparse
import logging
import os
from pathlib import Path
import signal
import sys

from ambient_canvas_theme import (
    compose_theme_source_identifier,
    resolve_theme_background_color,
)

from playback.display_ambient_canvas_loop import (
    DEFAULT_PLAYER_BINARY_PATH,
    launch_display,
)
from playback.player_diagnostics import create_diagnostic_logger
from playback.player_processes import (
    a_record_pass_is_running,
    is_display_running_for_loop,
    stop_every_display,
    wait_for_every_display_to_exit,
)
from recording.recorded_loop_capture_plan import (
    DEFAULT_CAPTURE_DURATION_SECONDS,
    DEFAULT_CAPTURE_FRAMES_PER_SECOND,
)
from recording.recorded_loop_capture_target import (
    compose_recorded_source_identifier,
    resolve_recorded_loop_capture_target,
)
from recording.recorded_segment_store import (
    read_recorded_source_identifier,
    resolve_playable_segment_manifest_path,
)
from render_ambient_canvas_loop import (
    render_recorded_loop,
    resolve_index_file_path,
)


LOGGER = logging.getLogger("ambient_canvas.launcher")


def recorded_loop_exists(loop_directory):
    return resolve_playable_segment_manifest_path(loop_directory) is not None


def recorded_loop_is_fresh(loop_directory, source_identifier):
    return read_recorded_source_identifier(
        loop_directory
    ) == source_identifier and recorded_loop_exists(loop_directory)


def ensure_screensaver(
    index_file_path,
    capture_target,
    source_identifier,
    theme_background_hex,
    player_binary_path,
    duration_seconds,
    frames_per_second,
):
    loop_directory = capture_target.loop_directory
    recorded_loop_was_replaced = False
    LOGGER.info(
        "launcher_check loop=%s source=%s player=%s",
        loop_directory,
        source_identifier,
        player_binary_path,
    )
    if not recorded_loop_is_fresh(loop_directory, source_identifier):
        if a_record_pass_is_running():
            LOGGER.info("recording_already_running")
            return 0
        LOGGER.info("recording_started loop=%s", loop_directory)
        rendered_manifest_path = render_recorded_loop(
            index_file_path,
            capture_target,
            source_identifier,
            duration_seconds,
            frames_per_second,
            theme_background_hex,
        )
        if rendered_manifest_path is None and not recorded_loop_exists(loop_directory):
            LOGGER.error("recording_failed_no_playable_loop loop=%s", loop_directory)
            return 1
        recorded_loop_was_replaced = rendered_manifest_path is not None
        LOGGER.info("recording_finished replaced=%s", recorded_loop_was_replaced)

    if not recorded_loop_was_replaced and is_display_running_for_loop(
        player_binary_path, loop_directory
    ):
        LOGGER.info("player_already_running loop=%s", loop_directory)
        return 0
    LOGGER.info("player_replacement_started loop=%s", loop_directory)
    stop_every_display(player_binary_path)
    wait_for_every_display_to_exit(player_binary_path)
    return launch_display(
        player_binary_path, loop_directory, capture_target.playback_dwell_override_path
    )


def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("--output-directory", required=True)
    argument_parser.add_argument("--source-identifier", required=True)
    argument_parser.add_argument("--theme-colors-path", required=True)
    argument_parser.add_argument("--player-binary", default=DEFAULT_PLAYER_BINARY_PATH)
    argument_parser.add_argument(
        "--seconds", type=int, default=DEFAULT_CAPTURE_DURATION_SECONDS
    )
    argument_parser.add_argument(
        "--fps", type=int, default=DEFAULT_CAPTURE_FRAMES_PER_SECOND
    )
    parsed_arguments = argument_parser.parse_args()
    create_diagnostic_logger(
        LOGGER.name, Path(parsed_arguments.output_directory) / "launcher.log"
    )
    LOGGER.info("launcher_started pid=%s", os.getpid())

    index_file_path = resolve_index_file_path()
    if index_file_path is None:
        LOGGER.error("web_assets_missing")
        print(
            "ensure-ambient-canvas-screensaver: web assets not found", file=sys.stderr
        )
        return 1

    capture_target = resolve_recorded_loop_capture_target(
        parsed_arguments.output_directory
    )
    theme_background_hex = resolve_theme_background_color(
        parsed_arguments.theme_colors_path
    )
    return ensure_screensaver(
        index_file_path,
        capture_target,
        compose_recorded_source_identifier(
            compose_theme_source_identifier(
                parsed_arguments.source_identifier, theme_background_hex
            ),
            capture_target.capture_signature,
        ),
        theme_background_hex,
        parsed_arguments.player_binary,
        parsed_arguments.seconds,
        parsed_arguments.fps,
    )


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *ignored: sys.exit(1))
    try:
        result = main()
    except Exception:
        LOGGER.exception("launcher_failed")
        result = 1
    LOGGER.info("launcher_finished exit_code=%s", result)
    sys.exit(result)
