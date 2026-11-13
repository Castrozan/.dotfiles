import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

SNAPSHOT_INGESTION_DIRECTORY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SNAPSHOT_INGESTION_DIRECTORY))


class RecordingIngestHandler(BaseHTTPRequestHandler):
    def do_PUT(self):
        self._answer_recorded_request()

    def do_POST(self):
        self._answer_recorded_request()

    def _answer_recorded_request(self):
        content_length = int(self.headers.get("content-length", 0))
        request_body = self.rfile.read(content_length)
        self.server.received_requests.append(
            {
                "method": self.command,
                "path": self.path,
                "headers": {
                    name.lower(): value for name, value in self.headers.items()
                },
                "body": request_body,
            }
        )
        self.send_response(self.server.reply_status)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(self.server.reply_body)

    def log_message(self, format, *arguments):
        return


@pytest.fixture
def ingest_loopback():
    server = HTTPServer(("127.0.0.1", 0), RecordingIngestHandler)
    server.received_requests = []
    server.reply_status = 202
    server.reply_body = json.dumps({"accepted": True}).encode("utf-8")
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture
def loopback_base_url(ingest_loopback):
    return f"http://127.0.0.1:{ingest_loopback.server_address[1]}/ingest"
