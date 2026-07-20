import argparse
import os
import shutil
import signal
import subprocess
import sys
import tempfile

from ambient_canvas_browser import (
    read_screen_dimensions,
    resolve_browser_executable_path,
    resolve_centered_window_geometry,
    resolve_chromium_browser_application,
)
from recorded_loop_capture_plan import (
    DEFAULT_CAPTURE_DURATION_SECONDS,
    DEFAULT_CAPTURE_FRAMES_PER_SECOND,
    build_record_browser_arguments,
    build_record_index_url,
    resolve_minimum_recorded_bytes,
    resolve_upload_wait_budget_seconds,
)
from recorded_loop_upload_server import (
    start_recorded_loop_upload_server,
    write_recorded_loop_pointer_files,
    write_recorded_loop_segment_table,
)
from scene_video_cache import (
    download_missing_scene_videos,
    resolve_scene_video_directory,
)


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


def render_recorded_loop(
    index_file_path,
    output_directory,
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

    os.makedirs(output_directory, exist_ok=True)
    served_web_directory = os.path.dirname(index_file_path)
    download_missing_scene_videos(served_web_directory, output_directory)
    upload_server = start_recorded_loop_upload_server(
        output_directory,
        served_web_directory,
        resolve_scene_video_directory(output_directory),
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
    )
    browser_process = subprocess.Popen(
        build_record_browser_arguments(
            resolve_browser_executable_path(browser_application),
            record_index_url,
            throwaway_profile_directory,
            resolve_centered_window_geometry(*read_screen_dimensions()),
        ),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        upload_arrived = upload_server.upload_completed_event.wait(
            resolve_upload_wait_budget_seconds(duration_seconds)
        )
    finally:
        terminate_browser_process(browser_process, throwaway_profile_directory)
        upload_server.shutdown()
        shutil.rmtree(throwaway_profile_directory, ignore_errors=True)

    staging_path = upload_server.received_staging_path
    if not upload_arrived or staging_path is None:
        print("render-ambient-canvas-loop: recording did not complete", file=sys.stderr)
        return None

    if os.path.getsize(staging_path) < resolve_minimum_recorded_bytes(duration_seconds):
        os.remove(staging_path)
        print(
            "render-ambient-canvas-loop: recording had too little motion",
            file=sys.stderr,
        )
        return None

    media_filename = f"loop.{upload_server.received_extension}"
    os.replace(staging_path, os.path.join(output_directory, media_filename))
    write_recorded_loop_segment_table(
        output_directory, upload_server.received_segment_table_bytes
    )
    write_recorded_loop_pointer_files(
        output_directory, media_filename, source_identifier
    )
    return media_filename


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

    media_filename = render_recorded_loop(
        index_file_path,
        parsed_arguments.output_directory,
        parsed_arguments.source_identifier,
        parsed_arguments.seconds,
        parsed_arguments.fps,
    )
    if media_filename is None:
        return 1
    print(os.path.join(parsed_arguments.output_directory, media_filename))
    return 0


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *ignored: sys.exit(1))
    sys.exit(main())
