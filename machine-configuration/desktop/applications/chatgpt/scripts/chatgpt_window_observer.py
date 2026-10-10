import json
import os
import select
import socket
import time
from pathlib import Path


def validate_client(client) -> None:
    if not isinstance(client, dict):
        raise ValueError("Invalid desktop client")
    if not isinstance(client.get("pid"), int):
        raise ValueError("Invalid desktop process identity")


def owned_window_address(client, process_ids: set[int]) -> str | None:
    validate_client(client)
    if client["pid"] not in process_ids or client.get("mapped") is False:
        return None
    address = client.get("address")
    if not isinstance(address, str):
        raise ValueError("Invalid desktop window address")
    return address.removeprefix("0x")


def owned_window_addresses(clients, process_ids: set[int]) -> set[str] | None:
    if not isinstance(clients, list):
        return None
    try:
        addresses = (owned_window_address(client, process_ids) for client in clients)
        return set(filter(lambda address: address is not None, addresses))
    except ValueError:
        return None


class ChatGPTWindowObserver:
    def __init__(self):
        runtime_directory = os.environ.get("XDG_RUNTIME_DIR")
        instance_signature = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
        self.socket_directory = (
            Path(runtime_directory) / "hypr" / instance_signature
            if runtime_directory and instance_signature
            else None
        )
        self.event_socket = None
        self.pending_events = b""
        self.refresh_needed = True
        self.window_open = None
        self.next_connection_attempt = 0

    def disconnect(self):
        if self.event_socket is not None:
            self.event_socket.close()
        self.event_socket = None
        self.pending_events = b""
        self.window_open = None
        self.refresh_needed = True
        self.next_connection_attempt = time.monotonic() + 5

    def connect_if_due(self):
        if self.event_socket is not None:
            return
        if self.socket_directory is None:
            return
        if time.monotonic() < self.next_connection_attempt:
            return
        self.connect()

    def connect(self):
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            connection.settimeout(1)
            connection.connect(str(self.socket_directory / ".socket2.sock"))
            connection.setblocking(False)
            self.event_socket = connection
            self.refresh_needed = True
        except OSError:
            connection.close()
            self.disconnect()

    def consume_events(self, data: bytes):
        lines = (self.pending_events + data).split(b"\n")
        self.pending_events = lines.pop()
        if any(
            line.partition(b">>")[0] in (b"openwindow", b"closewindow")
            for line in lines
        ):
            self.refresh_needed = True

    def receive_events(self):
        try:
            data = self.event_socket.recv(65536)
            if not data or len(self.pending_events) + len(data) > 131072:
                self.disconnect()
                return
            self.consume_events(data)
        except OSError:
            self.disconnect()

    def poll(self, timeout_seconds: float):
        self.connect_if_due()
        readable, _, _ = select.select(
            [self.event_socket] if self.event_socket else [], [], [], timeout_seconds
        )
        if readable:
            self.receive_events()

    def desktop_clients(self):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(1)
            connection.connect(str(self.socket_directory / ".socket.sock"))
            connection.sendall(b"j/clients")
            response = bytearray()
            while data := connection.recv(65536):
                response.extend(data)
                if len(response) > 2 * 1024**2:
                    raise ValueError("Desktop snapshot exceeded its bound")
        return json.loads(response)

    def refresh(self, process_ids: set[int]):
        self.refresh_needed = False
        if self.event_socket is None:
            self.window_open = None
            return
        try:
            addresses = owned_window_addresses(self.desktop_clients(), process_ids)
            self.window_open = None if addresses is None else bool(addresses)
        except (OSError, ValueError):
            self.disconnect()
