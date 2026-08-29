import json
import mimetypes
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from comet_stream_adapter import CometStreamAdapter
from managed_profile import (
    inject_managed_profile_script,
    render_managed_profile_script,
    select_streaming_server_url,
)
from managed_service_worker import render_managed_service_worker
from prowlarr_stream_provider import ProwlarrStreamProvider, read_prowlarr_api_key
from stremio_protocol import addon_manifest, parse_stream_request


class StremioRequestHandler(BaseHTTPRequestHandler):
    static_root: Path
    stream_provider: ProwlarrStreamProvider
    comet_adapter: CometStreamAdapter
    public_host: str
    public_streaming_server_url: str
    tailnet_streaming_server_url: str

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_HEAD(self):
        self._handle_request(False)

    def do_GET(self):
        self._handle_request(True)

    def _handle_request(self, include_body: bool):
        path = urllib.parse.urlsplit(self.path).path
        if path == "/healthz":
            self._send_json({"status": "ok"}, include_body)
            return
        if path == "/managed-profile.js":
            self._send_managed_profile(include_body)
            return
        if path == "/service-worker.js":
            self._send_managed_service_worker(include_body)
            return
        if path == "/prowlarr/manifest.json":
            self._send_json(addon_manifest(), include_body)
            return
        if path == "/comet" or path.startswith("/comet/"):
            self._send_comet(self.path.removeprefix("/comet") or "/", include_body)
            return
        stream_request = parse_stream_request(path)
        if stream_request is not None:
            try:
                streams = self.stream_provider.streams(stream_request)
            except Exception as error:
                print(f"stream lookup failed: {error}", file=sys.stderr, flush=True)
                streams = []
            self._send_json({"streams": streams}, include_body)
            return
        self._send_static(path, include_body)

    def _send_comet(self, request_target: str, include_body: bool):
        try:
            response = self.comet_adapter.response(request_target)
        except Exception as error:
            print(f"Comet proxy failed: {error}", file=sys.stderr, flush=True)
            self.send_error(502)
            return
        self.send_response(response.status)
        self._send_cors_headers()
        self.send_header("Content-Type", response.content_type)
        self.send_header("Cache-Control", response.cache_control or "no-store")
        if response.location is not None:
            self.send_header("Location", response.location)
        self.send_header("Content-Length", str(len(response.body)))
        self.end_headers()
        if include_body:
            self.wfile.write(response.body)

    def _send_json(self, payload: dict, include_body: bool):
        body = json.dumps(payload, separators=(",", ":")).encode()
        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if include_body:
            self.wfile.write(body)

    def _send_managed_profile(self, include_body: bool):
        streaming_server_url = select_streaming_server_url(
            self.headers.get("Host", "").strip(),
            self.public_host,
            self.tailnet_streaming_server_url,
            self.public_streaming_server_url,
        )
        body = render_managed_profile_script(streaming_server_url)
        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Type", "text/javascript; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if include_body:
            self.wfile.write(body)

    def _send_managed_service_worker(self, include_body: bool):
        body = render_managed_service_worker()
        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Type", "text/javascript; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Service-Worker-Allowed", "/")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if include_body:
            self.wfile.write(body)

    def _send_static(self, request_path: str, include_body: bool):
        relative_path = urllib.parse.unquote(request_path).lstrip("/") or "index.html"
        candidate = (self.static_root / relative_path).resolve()
        if not candidate.is_relative_to(self.static_root) or not candidate.is_file():
            self.send_error(404)
            return
        body = candidate.read_bytes()
        if candidate.name == "index.html":
            body = inject_managed_profile_script(body)
        self.send_response(200)
        self._send_cors_headers()
        self.send_header(
            "Content-Type",
            mimetypes.guess_type(candidate.name)[0] or "application/octet-stream",
        )
        cache_control = (
            "no-cache"
            if candidate.name == "index.html"
            else "public, max-age=31536000, immutable"
        )
        self.send_header("Cache-Control", cache_control)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if include_body:
            self.wfile.write(body)

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")


def required_environment_value(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def main():
    bind_address = required_environment_value("STREMIO_BIND_ADDRESS")
    port = int(required_environment_value("STREMIO_WEB_PORT"))
    public_web_url = required_environment_value("STREMIO_PUBLIC_WEB_URL")
    tailnet_streaming_server_url = required_environment_value(
        "STREMIO_TAILNET_STREAMING_SERVER_URL"
    )
    StremioRequestHandler.static_root = Path(
        required_environment_value("STREMIO_WEB_ROOT")
    ).resolve()
    StremioRequestHandler.stream_provider = ProwlarrStreamProvider(
        required_environment_value("STREMIO_PROWLARR_URL"),
        read_prowlarr_api_key(
            Path(required_environment_value("STREMIO_PROWLARR_CONFIG_FILE"))
        ),
        required_environment_value("STREMIO_METADATA_URL"),
    )
    StremioRequestHandler.comet_adapter = CometStreamAdapter(
        required_environment_value("STREMIO_COMET_URL")
    )
    StremioRequestHandler.public_host = urllib.parse.urlsplit(public_web_url).netloc
    StremioRequestHandler.public_streaming_server_url = (
        f"{public_web_url.rstrip('/')}/server/"
    )
    StremioRequestHandler.tailnet_streaming_server_url = tailnet_streaming_server_url
    server = ThreadingHTTPServer((bind_address, port), StremioRequestHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
