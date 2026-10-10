import json
import os
import select
import socket
import time
from pathlib import Path


def owned_window_addresses(clients, process_ids: set[int]) -> set[str] | None:
    if not isinstance(clients, list):
        return None
    addresses = set()
    for client in clients:
        if not isinstance(client, dict) or not isinstance(client.get("pid"), int):
            return None
        if client["pid"] not in process_ids or client.get("mapped") is False:
            continue
        address = client.get("address")
        if not isinstance(address, str):
            return None
        addresses.add(address.removeprefix("0x"))
    return addresses


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

    def poll(self, timeout_seconds: float):
        if (
            self.event_socket is None
            and self.socket_directory is not None
            and time.monotonic() >= self.next_connection_attempt
        ):
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
        readable, _, _ = select.select(
            [self.event_socket] if self.event_socket else [], [], [], timeout_seconds
        )
        if not readable:
            return
        try:
            data = self.event_socket.recv(65536)
            if not data or len(self.pending_events) + len(data) > 131072:
                self.disconnect()
                return
            lines = (self.pending_events + data).split(b"\n")
            self.pending_events = lines.pop()
            if any(
                line.partition(b">>")[0] in (b"openwindow", b"closewindow")
                for line in lines
            ):
                self.refresh_needed = True
        except OSError:
            self.disconnect()

    def refresh(self, process_ids: set[int]):
        self.refresh_needed = False
        if self.event_socket is None:
            self.window_open = None
            return
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                connection.settimeout(1)
                connection.connect(str(self.socket_directory / ".socket.sock"))
                connection.sendall(b"j/clients")
                response = bytearray()
                while data := connection.recv(65536):
                    response.extend(data)
                    if len(response) > 2 * 1024**2:
                        raise ValueError("Desktop snapshot exceeded its bound")
            addresses = owned_window_addresses(json.loads(response), process_ids)
            self.window_open = None if addresses is None else bool(addresses)
        except (OSError, ValueError):
            self.window_open = None
            self.disconnect()
