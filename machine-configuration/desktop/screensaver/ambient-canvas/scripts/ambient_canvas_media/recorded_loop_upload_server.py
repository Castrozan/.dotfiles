import functools
import http.server
import json
import os
import posixpath
import threading
import urllib.parse

from byte_range_request_handler import ByteRangeRequestHandler
from recorded_loop_capture_plan import resolve_minimum_recorded_bytes
from recorded_segment_store import (
    list_recorded_segment_fingerprints,
    store_recorded_segment,
)
from scene_source_digests import build_segment_fingerprint_inputs

SERVED_VIDEO_URL_PREFIX = "/ambient-canvas-videos/"
SEGMENT_FINGERPRINT_INVENTORY_URL = "/recorded-segment-fingerprints"
SEGMENT_FINGERPRINT_INPUTS_URL = "/segment-fingerprint-inputs"


class RecordedLoopRequestHandler(ByteRangeRequestHandler):
    def translate_path(self, path):
        requested_path = urllib.parse.urlparse(path).path
        if not requested_path.startswith(SERVED_VIDEO_URL_PREFIX):
            return super().translate_path(path)
        requested_filename = posixpath.basename(
            requested_path[len(SERVED_VIDEO_URL_PREFIX) :]
        )
        return os.path.join(self.server.served_video_directory, requested_filename)

    def do_GET(self):
        requested_path = urllib.parse.urlparse(self.path).path
        if requested_path == SEGMENT_FINGERPRINT_INVENTORY_URL:
            self.send_json_response(
                {"fingerprints": self.server.list_recorded_fingerprints()}
            )
            return
        if requested_path == SEGMENT_FINGERPRINT_INPUTS_URL:
            self.send_json_response(self.server.resolve_fingerprint_inputs())
            return
        super().do_GET()

    def do_POST(self):
        parsed_request = urllib.parse.urlparse(self.path)
        if parsed_request.path != "/upload":
            self.send_response(404)
            self.end_headers()
            return
        request_query = urllib.parse.parse_qs(parsed_request.query)
        content_length = int(self.headers.get("Content-Length", "0"))
        uploaded_bytes = self.rfile.read(content_length)
        if request_query.get("kind", [""])[0] == "manifest":
            self.server.receive_segment_manifest(uploaded_bytes)
            self.send_response(204)
            self.end_headers()
            return
        segment_was_stored = self.server.receive_recorded_segment(
            request_query.get("fingerprint", [""])[0],
            request_query.get("extension", ["mp4"])[0],
            float(request_query.get("seconds", ["0"])[0]),
            uploaded_bytes,
        )
        self.send_response(204 if segment_was_stored else 422)
        self.end_headers()

    def send_json_response(self, response_payload):
        encoded_payload = json.dumps(response_payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded_payload)))
        self.end_headers()
        self.wfile.write(encoded_payload)

    def log_message(self, *ignored_arguments):
        return


class RecordedLoopUploadServer(http.server.ThreadingHTTPServer):
    def __init__(self, output_directory, served_web_directory, served_video_directory):
        super().__init__(
            ("127.0.0.1", 0),
            functools.partial(
                RecordedLoopRequestHandler, directory=served_web_directory
            ),
        )
        self.served_web_directory = served_web_directory
        self.served_video_directory = served_video_directory
        self.output_directory = output_directory
        self.manifest_received_event = threading.Event()
        self.received_manifest_bytes = None
        self.rejected_segment_fingerprints = []

    @property
    def upload_port(self):
        return self.server_address[1]

    def list_recorded_fingerprints(self):
        return list_recorded_segment_fingerprints(self.output_directory)

    def resolve_fingerprint_inputs(self):
        return build_segment_fingerprint_inputs(self.served_web_directory)

    def receive_segment_manifest(self, manifest_bytes):
        self.received_manifest_bytes = manifest_bytes
        self.manifest_received_event.set()

    def receive_recorded_segment(
        self, segment_fingerprint, extension, duration_seconds, recorded_bytes
    ):
        if not segment_fingerprint or duration_seconds <= 0:
            return False
        if len(recorded_bytes) < resolve_minimum_recorded_bytes(duration_seconds):
            self.rejected_segment_fingerprints.append(segment_fingerprint)
            return False
        store_recorded_segment(
            self.output_directory, segment_fingerprint, extension, recorded_bytes
        )
        return True


def start_recorded_loop_upload_server(
    output_directory, served_web_directory, served_video_directory
):
    upload_server = RecordedLoopUploadServer(
        output_directory, served_web_directory, served_video_directory
    )
    server_thread = threading.Thread(target=upload_server.serve_forever, daemon=True)
    server_thread.start()
    return upload_server
