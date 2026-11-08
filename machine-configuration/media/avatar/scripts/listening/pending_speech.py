import threading


class PendingSpeech:
    def __init__(self, marker):
        self.marker = marker
        self.count = 0
        self.lock = threading.Lock()
        marker.unlink(missing_ok=True)

    def begin(self):
        with self.lock:
            self.count += 1
            self.marker.touch(mode=0o600)

    def finish(self):
        with self.lock:
            self.count -= 1
            if not self.count:
                self.marker.unlink(missing_ok=True)

    def clear(self):
        with self.lock:
            self.count = 0
            self.marker.unlink(missing_ok=True)
