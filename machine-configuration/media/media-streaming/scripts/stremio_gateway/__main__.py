import json
import mimetypes
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from prowlarr_stream_provider import ProwlarrStreamProvider, read_prowlarr_api_key
from stremio_protocol import (
    addon_manifest,
    parse_stream_request,
    setup_url_for_request_origin,
)


class StremioRequestHandler(BaseHTTPRequestHandler):
    static_root: Path
    stream_provider: ProwlarrStreamProvider
    public_host: str
    public_setup_redirect_url: str
    tailnet_setup_redirect_url: str

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
        if path == "/setup":
            self.send_response(302)
            request_host = self.headers.get("Host", "").strip()
            setup_redirect_url = (
                self.public_setup_redirect_url
                if request_host == self.public_host
                else self.tailnet_setup_redirect_url
            )
            self.send_header("Location", setup_redirect_url)
            self.end_headers()
            return
        if path == "/prowlarr/manifest.json":
            self._send_json(addon_manifest(), include_body)
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

    def _send_static(self, request_path: str, include_body: bool):
        relative_path = urllib.parse.unquote(request_path).lstrip("/") or "index.html"
        candidate = (self.static_root / relative_path).resolve()
        if not candidate.is_relative_to(self.static_root) or not candidate.is_file():
            self.send_error(404)
            return
        body = candidate.read_bytes()
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
    web_url = required_environment_value("STREMIO_WEB_URL")
    public_web_url = required_environment_value("STREMIO_PUBLIC_WEB_URL")
    streaming_server_url = required_environment_value("STREMIO_STREAMING_SERVER_URL")
    public_addon_manifest_url = required_environment_value(
        "STREMIO_PUBLIC_ADDON_MANIFEST_URL"
    )
    tailnet_addon_manifest_url = required_environment_value(
        "STREMIO_TAILNET_ADDON_MANIFEST_URL"
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
    StremioRequestHandler.public_host = urllib.parse.urlsplit(public_web_url).netloc
    StremioRequestHandler.public_setup_redirect_url = setup_url_for_request_origin(
        public_web_url,
        web_url,
        streaming_server_url,
        public_addon_manifest_url,
    )
    StremioRequestHandler.tailnet_setup_redirect_url = setup_url_for_request_origin(
        web_url,
        web_url,
        streaming_server_url,
        tailnet_addon_manifest_url,
    )
    server = ThreadingHTTPServer((bind_address, port), StremioRequestHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
