import concurrent.futures
import logging
import os
import sys
import threading
import time

from recording.recorded_loop_browser_capture import (
    BrowserCaptureRequest,
    drive_record_browser,
)
from recording.recorded_loop_capture_plan import (
    RecordingWorker,
    resolve_upload_wait_budget_seconds,
)
from recording.recorded_segment_manifest import parse_uploaded_segment_manifest


def resolve_recording_worker_count():
    return max(1, min(4, (os.cpu_count() or 1) // 2))


def capture_recorded_playlist(
    index_file_path,
    capture_target,
    browser_application,
    configuration,
):
    request = BrowserCaptureRequest(
        index_file_path, capture_target, browser_application, configuration
    )
    worker_count = resolve_recording_worker_count()
    logging.getLogger("ambient_canvas.launcher").info(
        "recording_pool_started workers=%s", worker_count
    )
    deadline = time.monotonic() + resolve_upload_wait_budget_seconds()
    cancellation_event = threading.Event()
    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
        try:
            recordings = [
                executor.submit(
                    drive_record_browser,
                    request,
                    RecordingWorker(worker_index, worker_count),
                    deadline,
                    cancellation_event,
                )
                for worker_index in range(worker_count)
            ]
            manifests = [recording.result() for recording in recordings]
        except Exception as recording_error:
            print(f"render-ambient-canvas-loop: {recording_error}", file=sys.stderr)
            return None
        finally:
            cancellation_event.set()

    segment_plans = [
        parse_uploaded_segment_manifest(manifest) for manifest in manifests
    ]
    if not segment_plans[0] or any(plan != segment_plans[0] for plan in segment_plans):
        return None
    return manifests[0]
