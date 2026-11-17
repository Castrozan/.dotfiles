import json
import os
import shutil
import socket
import tempfile
import threading


class FakeBridge:
    def __init__(self, play_reply=None, capture_bytes=b""):
        self.directory = tempfile.mkdtemp(prefix="vb")
        self.path = os.path.join(self.directory, "c.sock")
        self.requests = []
        self.uploads = []
        self.play_received = threading.Event()
        self.hush_received = threading.Event()
        self._play_reply = play_reply
        self._capture_bytes = capture_bytes
        self._listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._listener.bind(self.path)
        self._listener.listen()
        self._thread = threading.Thread(target=self._accept_forever, daemon=True)
        self._thread.start()

    def _accept_forever(self):
        while True:
            try:
                connection, _address = self._listener.accept()
            except OSError:
                return
            threading.Thread(
                target=self._serve, args=(connection,), daemon=True
            ).start()

    def _serve(self, connection):
        with connection, connection.makefile("rwb") as stream:
            request = json.loads(stream.readline())
            self.requests.append(request)
            handlers = {
                "play": self._play,
                "hush": self._hush,
                "capture": self._capture,
            }
            handlers[request["command"]](request, stream)

    def _play(self, request, stream):
        self.uploads.append(stream.read(request["byte_count"]))
        self.play_received.set()
        if self._play_reply is None:
            stream.read()
            return
        stream.write(json.dumps(self._play_reply).encode() + b"\n")
        stream.flush()

    def _hush(self, _request, stream):
        stream.write(b'{"outcome":"hushed"}\n')
        stream.flush()
        self.hush_received.set()

    def _capture(self, _request, stream):
        stream.write(self._capture_bytes)
        stream.flush()

    def close(self):
        self._listener.close()
        shutil.rmtree(self.directory, ignore_errors=True)
