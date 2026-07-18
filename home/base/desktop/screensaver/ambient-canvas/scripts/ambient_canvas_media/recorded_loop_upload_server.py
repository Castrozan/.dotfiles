import functools
import http.server
import os
import tempfile
import threading
import urllib.parse


class RecordedLoopRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        parsed_request = urllib.parse.urlparse(self.path)
        if parsed_request.path != "/upload":
            self.send_response(404)
            self.end_headers()
            return
        requested_extension = urllib.parse.parse_qs(parsed_request.query).get(
            "extension", ["webm"]
        )[0]
        content_length = int(self.headers.get("Content-Length", "0"))
        recorded_bytes = self.rfile.read(content_length)
        self.server.receive_recorded_loop(requested_extension, recorded_bytes)
        self.send_response(204)
        self.end_headers()

    def log_message(self, *ignored_arguments):
        return


class RecordedLoopUploadServer(http.server.ThreadingHTTPServer):
    def __init__(self, output_directory, served_web_directory):
        super().__init__(
            ("127.0.0.1", 0),
            functools.partial(
                RecordedLoopRequestHandler, directory=served_web_directory
            ),
        )
        self.output_directory = output_directory
        self.upload_completed_event = threading.Event()
        self.received_media_filename = None

    @property
    def upload_port(self):
        return self.server_address[1]

    def receive_recorded_loop(self, extension, recorded_bytes):
        media_filename = f"loop.{extension}"
        destination_path = os.path.join(self.output_directory, media_filename)
        temporary_descriptor, temporary_path = tempfile.mkstemp(
            dir=self.output_directory, suffix=f".{extension}.partial"
        )
        with os.fdopen(temporary_descriptor, "wb") as temporary_file:
            temporary_file.write(recorded_bytes)
        os.replace(temporary_path, destination_path)
        self.received_media_filename = media_filename
        self.upload_completed_event.set()


def start_recorded_loop_upload_server(output_directory, served_web_directory):
    upload_server = RecordedLoopUploadServer(output_directory, served_web_directory)
    server_thread = threading.Thread(target=upload_server.serve_forever, daemon=True)
    server_thread.start()
    return upload_server


def write_recorded_loop_pointer_files(
    output_directory, media_filename, source_identifier
):
    with open(os.path.join(output_directory, "loop.current"), "w") as pointer_file:
        pointer_file.write(media_filename + "\n")
    with open(os.path.join(output_directory, "loop.source"), "w") as source_file:
        source_file.write(source_identifier + "\n")
