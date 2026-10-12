import json
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from comet_proxy import proxy_comet_request
from comet_stream_adapter import CometStreamAdapter
from managed_profile import (
    inject_managed_profile_script,
    render_managed_profile_script,
    select_streaming_server_url,
)
from managed_service_worker import render_managed_service_worker
from prowlarr_stream_provider import ProwlarrStreamProvider, read_prowlarr_api_key
import static_assets
from stremio_runtime_configuration import (
    load_comet_adapter,
    required_environment_value,
)
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
        if self._handle_fixed_request(path, include_body):
            return
        if self._is_comet_route(path):
            proxy_comet_request(
                self, self.path.removeprefix("/comet") or "/", include_body
            )
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

    @staticmethod
    def _is_comet_route(path: str) -> bool:
        return path == "/comet" or path.startswith("/comet/")

    def _handle_fixed_request(self, path: str, include_body: bool) -> bool:
        if path == "/healthz":
            self._send_json({"status": "ok"}, include_body)
            return True
        if path == "/managed-profile.js":
            self._send_managed_profile(include_body)
            return True
        if path == "/service-worker.js":
            self._send_managed_service_worker(include_body)
            return True
        if path == "/prowlarr/manifest.json":
            self._send_json(addon_manifest(), include_body)
            return True
        return False

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
        self._send_javascript(
            render_managed_profile_script(streaming_server_url), include_body
        )

    def _send_managed_service_worker(self, include_body: bool):
        self._send_javascript(
            render_managed_service_worker(),
            include_body,
            {"Service-Worker-Allowed": "/"},
        )

    def _send_javascript(
        self, body: bytes, include_body: bool, extra_headers: dict | None = None
    ):
        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Type", "text/javascript; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if include_body:
            self.wfile.write(body)

    def _send_static(self, request_path: str, include_body: bool):
        candidate = static_assets.static_candidate(self.static_root, request_path)
        if candidate is None:
            self.send_error(404)
            return
        body = candidate.read_bytes()
        if candidate.name == "index.html":
            body = inject_managed_profile_script(body)
        self.send_response(200)
        self._send_cors_headers()
        self.send_header(
            "Content-Type",
            static_assets.content_type(candidate),
        )
        self.send_header("Cache-Control", static_assets.cache_control(candidate))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if include_body:
            self.wfile.write(body)

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")


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
    StremioRequestHandler.comet_adapter = load_comet_adapter()
    StremioRequestHandler.public_host = urllib.parse.urlsplit(public_web_url).netloc
    StremioRequestHandler.public_streaming_server_url = (
        f"{public_web_url.rstrip('/')}/server/"
    )
    StremioRequestHandler.tailnet_streaming_server_url = tailnet_streaming_server_url
    server = ThreadingHTTPServer((bind_address, port), StremioRequestHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
