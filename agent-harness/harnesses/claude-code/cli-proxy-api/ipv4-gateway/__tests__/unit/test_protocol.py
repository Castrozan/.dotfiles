import importlib.util
import socket
import socketserver
import threading
from pathlib import Path

GATEWAY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "cli_proxy_api_ipv4_gateway.py"
)
GATEWAY_SPECIFICATION = importlib.util.spec_from_file_location(
    "cli_proxy_api_ipv4_gateway_protocol", GATEWAY_PATH
)
assert GATEWAY_SPECIFICATION
assert GATEWAY_SPECIFICATION.loader
GATEWAY_MODULE = importlib.util.module_from_spec(GATEWAY_SPECIFICATION)
GATEWAY_SPECIFICATION.loader.exec_module(GATEWAY_MODULE)


class IPv4EchoRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        request = self.request.recv(1024)
        self.request.sendall(b"echo:" + request)


class IPv6OnlyEchoServer(socketserver.ThreadingTCPServer):
    address_family = socket.AF_INET6

    def server_bind(self):
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
        super().server_bind()


def start_server(server):
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    return server_thread


def stop_server(server, server_thread):
    server.shutdown()
    server.server_close()
    server_thread.join()


def receive_http_headers(connection):
    response = b""
    while b"\r\n\r\n" not in response:
        response += connection.recv(1024)
    return response


def test_connect_tunnel_relays_through_ipv4_when_the_hostname_has_multiple_families():
    echo_server = socketserver.ThreadingTCPServer(
        ("127.0.0.1", 0), IPv4EchoRequestHandler
    )
    gateway_server = GATEWAY_MODULE.IPv4ConnectProxyServer(
        ("127.0.0.1", 0), GATEWAY_MODULE.IPv4ConnectProxyRequestHandler
    )
    echo_thread = start_server(echo_server)
    gateway_thread = start_server(gateway_server)

    try:
        with socket.create_connection(gateway_server.server_address) as connection:
            echo_port = echo_server.server_address[1]
            connection.sendall(
                (
                    f"CONNECT localhost:{echo_port} HTTP/1.1\r\n"
                    f"Host: localhost:{echo_port}\r\n\r\n"
                ).encode()
            )
            response_headers = receive_http_headers(connection)

            assert response_headers.startswith(
                b"HTTP/1.1 200 Connection Established\r\n"
            )

            connection.sendall(b"payload")
            assert connection.recv(1024) == b"echo:payload"
    finally:
        stop_server(gateway_server, gateway_thread)
        stop_server(echo_server, echo_thread)


def test_does_not_fall_back_to_an_available_ipv6_target():
    ipv6_server = IPv6OnlyEchoServer(("::1", 0), IPv4EchoRequestHandler)
    gateway_server = GATEWAY_MODULE.IPv4ConnectProxyServer(
        ("127.0.0.1", 0), GATEWAY_MODULE.IPv4ConnectProxyRequestHandler
    )
    ipv6_thread = start_server(ipv6_server)
    gateway_thread = start_server(gateway_server)

    try:
        with socket.create_connection(gateway_server.server_address) as connection:
            ipv6_port = ipv6_server.server_address[1]
            connection.sendall(
                (
                    f"CONNECT localhost:{ipv6_port} HTTP/1.1\r\n"
                    f"Host: localhost:{ipv6_port}\r\n\r\n"
                ).encode()
            )
            response_headers = receive_http_headers(connection)

            assert response_headers.startswith(b"HTTP/1.1 502 Bad Gateway\r\n")
    finally:
        stop_server(gateway_server, gateway_thread)
        stop_server(ipv6_server, ipv6_thread)


def test_rejects_non_connect_proxy_requests():
    gateway_server = GATEWAY_MODULE.IPv4ConnectProxyServer(
        ("127.0.0.1", 0), GATEWAY_MODULE.IPv4ConnectProxyRequestHandler
    )
    gateway_thread = start_server(gateway_server)

    try:
        with socket.create_connection(gateway_server.server_address) as connection:
            connection.sendall(b"GET http://example.com/ HTTP/1.1\r\n\r\n")
            response_headers = receive_http_headers(connection)

            assert response_headers.startswith(b"HTTP/1.1 405 Method Not Allowed\r\n")
    finally:
        stop_server(gateway_server, gateway_thread)


def test_rejects_a_malformed_request_line():
    gateway_server = GATEWAY_MODULE.IPv4ConnectProxyServer(
        ("127.0.0.1", 0), GATEWAY_MODULE.IPv4ConnectProxyRequestHandler
    )
    gateway_thread = start_server(gateway_server)

    try:
        with socket.create_connection(gateway_server.server_address) as connection:
            connection.sendall(b"CONNECT only-two-parts\r\n\r\n")
            response_headers = receive_http_headers(connection)

            assert response_headers.startswith(b"HTTP/1.1 400 Bad Request\r\n")
    finally:
        stop_server(gateway_server, gateway_thread)


def test_returns_bad_gateway_for_an_invalid_connect_target():
    gateway_server = GATEWAY_MODULE.IPv4ConnectProxyServer(
        ("127.0.0.1", 0), GATEWAY_MODULE.IPv4ConnectProxyRequestHandler
    )
    gateway_thread = start_server(gateway_server)

    try:
        with socket.create_connection(gateway_server.server_address) as connection:
            connection.sendall(
                b"CONNECT localhost:not-a-port HTTP/1.1\r\n"
                b"Host: localhost:not-a-port\r\n\r\n"
            )
            response_headers = receive_http_headers(connection)

            assert response_headers.startswith(b"HTTP/1.1 502 Bad Gateway\r\n")
    finally:
        stop_server(gateway_server, gateway_thread)
