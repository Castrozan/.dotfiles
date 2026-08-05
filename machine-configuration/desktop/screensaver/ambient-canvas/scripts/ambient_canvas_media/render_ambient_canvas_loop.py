import argparse
import os
import shutil
import signal
import subprocess
import sys
import tempfile

from ambient_canvas_browser import (
    resolve_browser_executable_path,
    resolve_centered_window_geometry,
    resolve_chromium_browser_application,
)
from recorded_loop_capture_plan import (
    DEFAULT_CAPTURE_DURATION_SECONDS,
    DEFAULT_CAPTURE_FRAMES_PER_SECOND,
    build_record_browser_arguments,
    build_record_index_url,
    resolve_upload_wait_budget_seconds,
)
from recorded_loop_capture_target import (
    compose_recorded_source_identifier,
    resolve_recorded_loop_capture_target,
)
from recorded_loop_upload_server import start_recorded_loop_upload_server
from recorded_segment_store import (
    build_recorded_segment_manifest,
    list_missing_manifest_segment_positions,
    parse_uploaded_segment_manifest,
    prune_recorded_segments_outside_manifest,
    write_recorded_segment_manifest,
    write_recorded_source_identifier,
)
from scene_video_cache import download_missing_scene_videos


def terminate_browser_process(browser_process, throwaway_profile_directory):
    try:
        browser_process.terminate()
        browser_process.wait(timeout=5)
    except (subprocess.TimeoutExpired, ProcessLookupError, OSError):
        try:
            browser_process.kill()
        except OSError:
            pass
    subprocess.run(
        ["/usr/bin/pkill", "-f", throwaway_profile_directory],
        check=False,
        capture_output=True,
    )


def drive_record_browser(
    index_file_path,
    capture_target,
    browser_application,
    duration_seconds,
    frames_per_second,
):
    served_web_directory = os.path.dirname(index_file_path)
    download_missing_scene_videos(
        served_web_directory, capture_target.scene_video_directory
    )
    upload_server = start_recorded_loop_upload_server(
        capture_target.loop_directory,
        served_web_directory,
        capture_target.scene_video_directory,
    )
    throwaway_profile_directory = tempfile.mkdtemp(prefix="ambient-canvas-record-")
    record_page_url = (
        f"http://127.0.0.1:{upload_server.upload_port}/"
        f"{os.path.basename(index_file_path)}"
    )
    record_index_url = build_record_index_url(
        record_page_url,
        f"http://127.0.0.1:{upload_server.upload_port}/upload",
        duration_seconds,
        frames_per_second,
        capture_target.capture_pixel_dimensions,
    )
    browser_process = subprocess.Popen(
        build_record_browser_arguments(
            resolve_browser_executable_path(browser_application),
            record_index_url,
            throwaway_profile_directory,
            resolve_centered_window_geometry(*capture_target.screen_dimensions),
        ),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        upload_server.manifest_received_event.wait(resolve_upload_wait_budget_seconds())
    finally:
        terminate_browser_process(browser_process, throwaway_profile_directory)
        upload_server.shutdown()
        shutil.rmtree(throwaway_profile_directory, ignore_errors=True)

    return upload_server


def commit_recorded_segment_manifest(
    output_directory, uploaded_manifest_bytes, source_identifier
):
    uploaded_segments = parse_uploaded_segment_manifest(uploaded_manifest_bytes)
    if uploaded_segments is None:
        print("render-ambient-canvas-loop: recording did not complete", file=sys.stderr)
        return None
    recorded_manifest = build_recorded_segment_manifest(uploaded_segments)
    missing_positions = list_missing_manifest_segment_positions(
        output_directory, recorded_manifest
    )
    if missing_positions:
        print(
            "render-ambient-canvas-loop: no segment was stored for playlist "
            f"composition {', '.join(str(position) for position in missing_positions)}",
            file=sys.stderr,
        )
        return None
    manifest_path = write_recorded_segment_manifest(output_directory, recorded_manifest)
    prune_recorded_segments_outside_manifest(output_directory, recorded_manifest)
    write_recorded_source_identifier(output_directory, source_identifier)
    return manifest_path


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
    upload_server = drive_record_browser(
        index_file_path,
        capture_target,
        browser_application,
        duration_seconds,
        frames_per_second,
    )
    return commit_recorded_segment_manifest(
        capture_target.loop_directory,
        upload_server.received_manifest_bytes,
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
    print(manifest_path)
    return 0


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *ignored: sys.exit(1))
    sys.exit(main())
