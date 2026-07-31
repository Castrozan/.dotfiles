import http.server
import os
import urllib.error
import urllib.request

DEFAULT_UPSTREAM_BASE_URL = "https://opencode.ai/zen"
DEFAULT_LISTEN_PORT = 18790
UPSTREAM_USER_AGENT = "opencode-zen-anonymous-proxy/1.0"
RESPONSE_CHUNK_SIZE = 8192
REQUEST_HEADERS_WORTH_FORWARDING = frozenset({"content-type", "accept"})
RESPONSE_HEADERS_WORTH_RELAYING = frozenset({"content-type"})


def upstream_base_url_from_environment():
    return os.environ.get("OPENCODE_ZEN_UPSTREAM_BASE_URL", DEFAULT_UPSTREAM_BASE_URL)


def listen_port_from_environment():
    return int(os.environ.get("OPENCODE_ZEN_PROXY_PORT", DEFAULT_LISTEN_PORT))


class AnonymousZenProxyHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        self.relay_to_upstream(None)

    def do_POST(self):
        declared_body_length = int(self.headers.get("content-length") or 0)
        self.relay_to_upstream(self.rfile.read(declared_body_length))

    def relay_to_upstream(self, request_body):
        upstream_request = urllib.request.Request(
            upstream_base_url_from_environment() + self.path,
            data=request_body,
            method=self.command,
            headers={
                "user-agent": UPSTREAM_USER_AGENT,
                **{
                    header_name: header_value
                    for header_name, header_value in self.headers.items()
                    if header_name.lower() in REQUEST_HEADERS_WORTH_FORWARDING
                },
            },
        )
        try:
            with urllib.request.urlopen(upstream_request) as upstream_response:
                self.stream_response_back(upstream_response)
        except urllib.error.HTTPError as refused_upstream_response:
            with refused_upstream_response:
                self.stream_response_back(refused_upstream_response)
        except OSError as unreachable_upstream:
            self.send_error(502, str(unreachable_upstream))

    def stream_response_back(self, upstream_response):
        self.send_response(upstream_response.status)
        for header_name, header_value in upstream_response.headers.items():
            if header_name.lower() in RESPONSE_HEADERS_WORTH_RELAYING:
                self.send_header(header_name, header_value)
        self.send_header("transfer-encoding", "chunked")
        self.end_headers()
        while True:
            response_chunk = upstream_response.read1(RESPONSE_CHUNK_SIZE)
            if not response_chunk:
                break
            self.wfile.write(b"%x\r\n%s\r\n" % (len(response_chunk), response_chunk))
            self.wfile.flush()
        self.wfile.write(b"0\r\n\r\n")
        self.wfile.flush()


def main():
    http.server.ThreadingHTTPServer(
        ("127.0.0.1", listen_port_from_environment()), AnonymousZenProxyHandler
    ).serve_forever()


if __name__ == "__main__":
    main()
