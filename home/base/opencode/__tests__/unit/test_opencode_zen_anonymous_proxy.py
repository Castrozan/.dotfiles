import http.client
import http.server
import json
import threading

import opencode_zen_anonymous_proxy as proxy


class RecordingUpstreamHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    received_headers = {}

    def do_POST(self):
        RecordingUpstreamHandler.received_headers = dict(self.headers)
        response_body = json.dumps({"echoed": "ok"}).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)

    def log_message(self, message_format, *arguments):
        return


def serve_in_background(server):
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    return server_thread


def post_through_proxy(proxy_port, headers):
    connection = http.client.HTTPConnection("127.0.0.1", proxy_port, timeout=10)
    connection.request("POST", "/v1/chat/completions", body=b"{}", headers=headers)
    response = connection.getresponse()
    body = response.read()
    connection.close()
    return response.status, body


def test_the_proxy_reaches_the_upstream_without_the_callers_authorization(monkeypatch):
    upstream = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), RecordingUpstreamHandler
    )
    serve_in_background(upstream)
    monkeypatch.setenv(
        "OPENCODE_ZEN_UPSTREAM_BASE_URL",
        f"http://127.0.0.1:{upstream.server_address[1]}",
    )

    proxy_server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), proxy.AnonymousZenProxyHandler
    )
    serve_in_background(proxy_server)

    status, body = post_through_proxy(
        proxy_server.server_address[1],
        {
            "content-type": "application/json",
            "authorization": "Bearer a-key-zen-never-issued",
        },
    )

    upstream.shutdown()
    upstream.server_close()
    proxy_server.shutdown()
    proxy_server.server_close()

    forwarded_headers = {
        name.lower(): value
        for name, value in RecordingUpstreamHandler.received_headers.items()
    }
    assert status == 200
    assert json.loads(body) == {"echoed": "ok"}
    assert "authorization" not in forwarded_headers
    assert forwarded_headers["user-agent"] == proxy.UPSTREAM_USER_AGENT
    assert forwarded_headers["content-type"] == "application/json"


def test_the_listen_port_falls_back_to_the_declared_default(monkeypatch):
    monkeypatch.delenv("OPENCODE_ZEN_PROXY_PORT", raising=False)
    assert proxy.listen_port_from_environment() == proxy.DEFAULT_LISTEN_PORT
    monkeypatch.setenv("OPENCODE_ZEN_PROXY_PORT", "18999")
    assert proxy.listen_port_from_environment() == 18999


def test_the_upstream_defaults_to_zen_when_the_environment_is_silent(monkeypatch):
    monkeypatch.delenv("OPENCODE_ZEN_UPSTREAM_BASE_URL", raising=False)
    assert proxy.upstream_base_url_from_environment() == proxy.DEFAULT_UPSTREAM_BASE_URL
