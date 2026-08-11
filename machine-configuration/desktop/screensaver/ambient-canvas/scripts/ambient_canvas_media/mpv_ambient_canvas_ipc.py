import json
import socket
import time
from typing import Optional

MPV_JSON_IPC_MESSAGE_DELIMITER = "\n"
MPV_IPC_RECONNECT_ATTEMPTS = 20
MPV_IPC_RECONNECT_INTERVAL_SECONDS = 0.2
MPV_IPC_READ_TIMEOUT_SECONDS = 5.0


class MpvIpcClient:
    def __init__(self, socket_path):
        self.socket_path = socket_path
        self._socket: Optional[socket.socket] = None
        self._buffer = b""

    def connect(self):
        for _ in range(MPV_IPC_RECONNECT_ATTEMPTS):
            try:
                self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self._socket.connect(self.socket_path)
                return self
            except (ConnectionRefusedError, FileNotFoundError):
                if self._socket is not None:
                    self._socket.close()
                time.sleep(MPV_IPC_RECONNECT_INTERVAL_SECONDS)
        raise ConnectionError(f"mpv IPC socket {self.socket_path} never appeared")

    def close(self):
        if self._socket is not None:
            self._socket.close()
            self._socket = None

    def send_command(self, command):
        if self._socket is None:
            raise ConnectionError("mpv IPC socket is not connected")
        self._socket.sendall(
            (json.dumps({"command": command}) + MPV_JSON_IPC_MESSAGE_DELIMITER).encode()
        )

    def read_event(self):
        if self._socket is None:
            return None
        self._socket.settimeout(MPV_IPC_READ_TIMEOUT_SECONDS)
        while True:
            event = self._read_available_line()
            if event is not None:
                return event
            try:
                chunk = self._socket.recv(65536)
            except socket.timeout:
                return None
            if not chunk:
                raise ConnectionError("mpv IPC socket closed")
            self._buffer += chunk

    def _read_available_line(self):
        newline_index = self._buffer.find(MPV_JSON_IPC_MESSAGE_DELIMITER.encode())
        if newline_index == -1:
            return None
        line_bytes = self._buffer[: newline_index + 1]
        self._buffer = self._buffer[newline_index + 1 :]
        try:
            return json.loads(line_bytes.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {"event": "unparseable"}


def wait_for_end_of_file(mpv_client):
    while True:
        event = mpv_client.read_event()
        if event is None:
            continue
        if event.get("event") == "end-file":
            return
