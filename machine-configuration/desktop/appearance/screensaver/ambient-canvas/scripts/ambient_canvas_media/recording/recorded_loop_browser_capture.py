import os
import shutil
import subprocess
import tempfile
import time
from typing import NamedTuple

from ambient_canvas_browser import (
    resolve_browser_executable_path,
    resolve_centered_window_geometry,
)
from recording.recorded_loop_capture_plan import (
    build_record_browser_arguments,
    build_record_index_url,
    RecordingConfiguration,
)
from recording.recorded_loop_capture_target import RecordedLoopCaptureTarget
from recorded_loop_upload_server import start_recorded_loop_upload_server


class BrowserCaptureRequest(NamedTuple):
    index_file_path: str
    capture_target: RecordedLoopCaptureTarget
    browser_application: str
    configuration: RecordingConfiguration


def terminate_browser_process(browser_process, throwaway_profile_directory):
    try:
        browser_process.terminate()
        browser_process.wait(timeout=5)
    except (subprocess.TimeoutExpired, OSError):
        try:
            browser_process.kill()
        except OSError:
            pass
    subprocess.run(
        [shutil.which("pkill") or "/usr/bin/pkill", "-f", throwaway_profile_directory],
        check=False,
        capture_output=True,
    )


def drive_record_browser(request, worker, deadline, cancellation_event):
    index_file_path = request.index_file_path
    capture_target = request.capture_target
    served_web_directory = os.path.dirname(index_file_path)
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
        capture_target.capture_pixel_dimensions,
        request.configuration,
        worker,
    )
    browser_process = None
    try:
        browser_process = subprocess.Popen(
            build_record_browser_arguments(
                resolve_browser_executable_path(request.browser_application),
                record_index_url,
                throwaway_profile_directory,
                resolve_centered_window_geometry(*capture_target.screen_dimensions),
            ),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        while not cancellation_event.is_set():
            remaining_seconds = deadline - time.monotonic()
            if remaining_seconds <= 0:
                break
            if upload_server.manifest_received_event.wait(min(1, remaining_seconds)):
                break
    finally:
        if browser_process is not None:
            terminate_browser_process(browser_process, throwaway_profile_directory)
        upload_server.shutdown()
        upload_server.server_close()
        shutil.rmtree(throwaway_profile_directory, ignore_errors=True)

    return upload_server.received_manifest_bytes
