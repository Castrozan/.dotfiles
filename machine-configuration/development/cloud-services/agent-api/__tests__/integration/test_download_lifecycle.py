import http.server
import threading

from agent_api.contract import OperationRequest
from agent_api.providers.downloading import DownloadProvider


def test_successful_single_download_returns_its_artifact(tmp_path):
    payload = b"fixture-media-payload"

    class MediaHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *arguments):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), MediaHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        request = OperationRequest(
            "download.media", {"url": f"http://127.0.0.1:{server.server_port}/clip.mp4"}
        )
        result = DownloadProvider().execute(request, tmp_path, "fixture")
        assert (tmp_path / result["artifact"]).read_bytes() == payload
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
