import json
import socket
import threading
from pathlib import Path

from hook_module_loader import HOOK_SUBPROCESS_TIMEOUT_SECONDS

ACCEPT_POLL_SECONDS = 0.05
REQUEST_READ_BYTES = 65536


class RecordingHerdrSocketServer:
    def __init__(self, socket_path: Path):
        self.results_by_method = {}
        self.received_requests = []
        self.serving = True
        self.socket_path = socket_path
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listener.bind(str(socket_path))
        self.listener.listen(8)
        self.listener.settimeout(ACCEPT_POLL_SECONDS)
        self.serving_thread = threading.Thread(target=self.serve_requests, daemon=True)
        self.serving_thread.start()

    def answer(self, method, result):
        self.results_by_method[method] = result

    def serve_requests(self):
        while self.serving:
            try:
                connection, _ = self.listener.accept()
            except OSError:
                continue
            with connection:
                connection.settimeout(HOOK_SUBPROCESS_TIMEOUT_SECONDS)
                self.answer_one_request(connection)

    def answer_one_request(self, connection):
        try:
            received_bytes = connection.recv(REQUEST_READ_BYTES).decode()
            if not received_bytes.strip():
                return
            request = json.loads(received_bytes)
            self.received_requests.append(request)
            response = {
                "id": request["id"],
                "result": self.results_by_method.get(request["method"], {}),
            }
            connection.sendall((json.dumps(response) + "\n").encode())
        except (KeyError, OSError, ValueError):
            return

    def requests_for(self, method):
        return [
            request for request in self.received_requests if request["method"] == method
        ]

    def close(self):
        self.serving = False
        self.serving_thread.join(timeout=HOOK_SUBPROCESS_TIMEOUT_SECONDS)
        self.listener.close()
