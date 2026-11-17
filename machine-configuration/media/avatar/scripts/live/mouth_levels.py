import array
import collections
import contextlib
import json
import math
import threading
import time

from websockets.exceptions import WebSocketException
from websockets.sync.client import connect

CONTROL_URL = "ws://127.0.0.1:8765"
CONNECT_TIMEOUT_SECONDS = 5
PAGE_PLAYBACK_DELAY_SECONDS = 0.3
IDLE_SECONDS = 0.15
FULL_SCALE = 32768
CONNECTION_FAILURES = (OSError, WebSocketException)


def open_control_connection():
    connection = connect(CONTROL_URL, open_timeout=CONNECT_TIMEOUT_SECONDS)
    connection.send(json.dumps({"type": "identify", "role": "agent"}))
    return connection


def level_of(pcm):
    samples = array.array("h")
    samples.frombytes(pcm[: len(pcm) - len(pcm) % 2])
    if not samples:
        return 0.0
    power = sum(sample * sample for sample in samples) / len(samples)
    return min(1.0, math.sqrt(power) / FULL_SCALE)


class MouthLevels:
    def __init__(self, connection, clock=time.monotonic):
        self.connection = connection
        self.clock = clock
        self.pending = collections.deque()
        self.shown = 0.0
        self.shown_at = clock()
        self.failure = None
        self.arrived = threading.Event()
        self.stopped = threading.Event()

    def start(self):
        threading.Thread(target=self.deliver_until_stopped, daemon=True).start()

    def show(self, pcm):
        due = self.clock() + PAGE_PLAYBACK_DELAY_SECONDS
        self.pending.append((due, level_of(pcm)))
        self.arrived.set()

    def silence(self):
        self.pending.clear()
        self.send(0.0)

    def send(self, level):
        self.connection.send(json.dumps({"type": "voiceLevel", "value": level}))
        self.shown = level
        self.shown_at = self.clock()

    def seconds_until_next_delivery(self):
        now = self.clock()
        if self.pending:
            return max(0.0, self.pending[0][0] - now)
        if self.shown:
            return max(0.0, self.shown_at + IDLE_SECONDS - now)
        return None

    def deliver_due(self):
        now = self.clock()
        while self.pending and self.pending[0][0] <= now:
            self.send(self.pending.popleft()[1])
        if self.mouth_is_idle(now):
            self.send(0.0)

    def mouth_is_idle(self, now):
        return not self.pending and self.shown and now - self.shown_at >= IDLE_SECONDS

    def deliver_until_stopped(self):
        try:
            while not self.stopped.is_set():
                self.arrived.clear()
                self.arrived.wait(self.seconds_until_next_delivery())
                self.deliver_due()
        except CONNECTION_FAILURES as error:
            self.failure = error

    def close(self):
        self.stopped.set()
        self.arrived.set()
        self.pending.clear()
        with contextlib.suppress(*CONNECTION_FAILURES):
            self.send(0.0)
        self.connection.close()
