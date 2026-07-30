import selectors
import socket
import socketserver
import subprocess
import sys
import threading
from collections.abc import Callable, Sequence

MAXIMUM_HTTP_LINE_BYTES = 65536
MAXIMUM_HTTP_HEADER_COUNT = 100
SOCKET_COPY_BUFFER_BYTES = 65536
UPSTREAM_CONNECTION_TIMEOUT_SECONDS = 30


class IPv4ConnectProxyServer(socketserver.ThreadingTCPServer):
    address_family = socket.AF_INET
    allow_reuse_address = True
    daemon_threads = True


def parse_connect_target(request_target: str) -> tuple[str, int]:
    hostname, separator, port_text = request_target.rpartition(":")
    if not separator or not hostname or ":" in hostname:
        raise ValueError("invalid CONNECT target")

    port = int(port_text)
    if not 1 <= port <= 65535:
        raise ValueError("invalid CONNECT port")

    return hostname, port


def connect_to_ipv4_upstream(hostname: str, port: int) -> socket.socket:
    upstream_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    upstream_connection.settimeout(UPSTREAM_CONNECTION_TIMEOUT_SECONDS)
    try:
        upstream_connection.connect((hostname, port))
    except OSError:
        upstream_connection.close()
        raise
    upstream_connection.settimeout(None)
    return upstream_connection


def relay_bidirectionally(
    first_connection: socket.socket, second_connection: socket.socket
) -> None:
    with selectors.DefaultSelector() as connection_selector:
        connection_selector.register(
            first_connection, selectors.EVENT_READ, second_connection
        )
        connection_selector.register(
            second_connection, selectors.EVENT_READ, first_connection
        )

        while connection_selector.get_map():
            for selection_key, _ in connection_selector.select():
                source_connection = selection_key.fileobj
                destination_connection = selection_key.data
                try:
                    payload = source_connection.recv(SOCKET_COPY_BUFFER_BYTES)
                except OSError:
                    return

                if payload:
                    try:
                        destination_connection.sendall(payload)
                    except OSError:
                        return
                    continue

                connection_selector.unregister(source_connection)
                try:
                    destination_connection.shutdown(socket.SHUT_WR)
                except OSError:
                    pass


class IPv4ConnectProxyRequestHandler(socketserver.StreamRequestHandler):
    def send_response(self, status_code: int, reason: str) -> None:
        self.wfile.write(
            (
                f"HTTP/1.1 {status_code} {reason}\r\n"
                "Connection: close\r\n"
                "Content-Length: 0\r\n\r\n"
            ).encode()
        )
        self.wfile.flush()

    def read_request_line(self) -> tuple[str, str, str]:
        request_line = self.rfile.readline(MAXIMUM_HTTP_LINE_BYTES + 1)
        if len(request_line) > MAXIMUM_HTTP_LINE_BYTES or not request_line.endswith(
            b"\n"
        ):
            raise ValueError("invalid request line")

        request_parts = request_line.decode("ascii").rstrip("\r\n").split()
        if len(request_parts) != 3:
            raise ValueError("invalid request line")

        return request_parts

    def discard_request_headers(self) -> None:
        for _ in range(MAXIMUM_HTTP_HEADER_COUNT):
            header_line = self.rfile.readline(MAXIMUM_HTTP_LINE_BYTES + 1)
            if len(header_line) > MAXIMUM_HTTP_LINE_BYTES:
                raise ValueError("header line too long")
            if header_line in (b"\r\n", b"\n"):
                return
            if not header_line.endswith(b"\n"):
                raise ValueError("invalid header line")

        raise ValueError("too many headers")

    def handle(self) -> None:
        try:
            request_method, request_target, http_version = self.read_request_line()
            self.discard_request_headers()
        except (UnicodeDecodeError, ValueError):
            self.send_response(400, "Bad Request")
            return

        if request_method != "CONNECT":
            self.send_response(405, "Method Not Allowed")
            return

        if http_version not in ("HTTP/1.0", "HTTP/1.1"):
            self.send_response(400, "Bad Request")
            return

        try:
            hostname, port = parse_connect_target(request_target)
            upstream_connection = connect_to_ipv4_upstream(hostname, port)
        except (OSError, ValueError):
            self.send_response(502, "Bad Gateway")
            return

        with upstream_connection:
            self.wfile.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            self.wfile.flush()
            relay_bidirectionally(self.connection, upstream_connection)


def run_cli_proxy_api_with_ipv4_gateway(
    listen_address: str,
    listen_port: int,
    program_arguments: Sequence[str],
    server_factory: Callable[
        [
            tuple[str, int],
            type[IPv4ConnectProxyRequestHandler],
        ],
        IPv4ConnectProxyServer,
    ] = IPv4ConnectProxyServer,
    process_factory: Callable[
        [Sequence[str]], subprocess.Popen[bytes]
    ] = subprocess.Popen,
) -> int:
    with server_factory(
        (listen_address, listen_port), IPv4ConnectProxyRequestHandler
    ) as gateway_server:
        gateway_thread = threading.Thread(
            target=gateway_server.serve_forever, daemon=True
        )
        gateway_thread.start()

        try:
            proxy_process = process_factory(program_arguments)
            return proxy_process.wait()
        finally:
            gateway_server.shutdown()
            gateway_thread.join()


def main() -> int:
    if len(sys.argv) < 4:
        return 2

    return run_cli_proxy_api_with_ipv4_gateway(
        sys.argv[1],
        int(sys.argv[2]),
        sys.argv[3:],
    )


if __name__ == "__main__":
    sys.exit(main())
