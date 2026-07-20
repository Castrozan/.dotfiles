import functools
import http.server
import os
import posixpath
import tempfile
import threading
import urllib.parse

from byte_range_request_handler import ByteRangeRequestHandler

SERVED_VIDEO_URL_PREFIX = "/ambient-canvas-videos/"


class RecordedLoopRequestHandler(ByteRangeRequestHandler):
    def translate_path(self, path):
        requested_path = urllib.parse.urlparse(path).path
        if not requested_path.startswith(SERVED_VIDEO_URL_PREFIX):
            return super().translate_path(path)
        requested_filename = posixpath.basename(
            requested_path[len(SERVED_VIDEO_URL_PREFIX) :]
        )
        return os.path.join(self.server.served_video_directory, requested_filename)

    def do_POST(self):
        parsed_request = urllib.parse.urlparse(self.path)
        if parsed_request.path != "/upload":
            self.send_response(404)
            self.end_headers()
            return
        request_query = urllib.parse.parse_qs(parsed_request.query)
        content_length = int(self.headers.get("Content-Length", "0"))
        uploaded_bytes = self.rfile.read(content_length)
        if request_query.get("kind", [""])[0] == "segments":
            self.server.receive_segment_table(uploaded_bytes)
        else:
            self.server.receive_recorded_loop(
                request_query.get("extension", ["webm"])[0], uploaded_bytes
            )
        self.send_response(204)
        self.end_headers()

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
        self.served_video_directory = served_video_directory
        self.output_directory = output_directory
        self.upload_completed_event = threading.Event()
        self.received_extension = None
        self.received_staging_path = None
        self.received_segment_table_bytes = None

    @property
    def upload_port(self):
        return self.server_address[1]

    def receive_segment_table(self, segment_table_bytes):
        self.received_segment_table_bytes = segment_table_bytes

    def receive_recorded_loop(self, extension, recorded_bytes):
        staging_descriptor, staging_path = tempfile.mkstemp(
            dir=self.output_directory, suffix=f".{extension}.staging"
        )
        with os.fdopen(staging_descriptor, "wb") as staging_file:
            staging_file.write(recorded_bytes)
        self.received_extension = extension
        self.received_staging_path = staging_path
        self.upload_completed_event.set()


def start_recorded_loop_upload_server(
    output_directory, served_web_directory, served_video_directory
):
    upload_server = RecordedLoopUploadServer(
        output_directory, served_web_directory, served_video_directory
    )
    server_thread = threading.Thread(target=upload_server.serve_forever, daemon=True)
    server_thread.start()
    return upload_server


def write_recorded_loop_segment_table(output_directory, segment_table_bytes):
    segment_table_path = os.path.join(output_directory, "loop.segments.json")
    if not segment_table_bytes:
        if os.path.exists(segment_table_path):
            os.remove(segment_table_path)
        return
    with open(segment_table_path, "wb") as segment_table_file:
        segment_table_file.write(segment_table_bytes)


def write_recorded_loop_pointer_files(
    output_directory, media_filename, source_identifier
):
    with open(os.path.join(output_directory, "loop.current"), "w") as pointer_file:
        pointer_file.write(media_filename + "\n")
    with open(os.path.join(output_directory, "loop.source"), "w") as source_file:
        source_file.write(source_identifier + "\n")
