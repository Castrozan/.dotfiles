import contextlib
import json
import threading
import time
from types import SimpleNamespace
from unittest.mock import patch

import mac_room_audio
import mouth_levels
from room_audio import LIP_SYNC_SINK

RATE = 24000


class Stream:
    def __init__(self):
        self.sent = []
        self.sent_at = []
        self.cleared = 0
        self.closed = False
        self.failure = None
        self.opening = threading.Event()
        self.opening.set()

    def open(self):
        self.opening.wait(5)

    def send(self, chunk):
        if self.failure:
            raise self.failure
        self.sent.append(chunk)
        self.sent_at.append(time.monotonic())

    def clear(self):
        self.cleared += 1

    def close(self):
        self.closed = True


class Connection:
    def __init__(self):
        self.sent = []
        self.closed = False
        self.failure = None

    def send(self, message):
        if self.failure:
            raise self.failure
        self.sent.append(json.loads(message))

    def close(self):
        self.closed = True

    def levels(self):
        return [message["value"] for message in self.sent]


def eventually(condition, seconds=3):
    deadline = time.monotonic() + seconds
    while not condition():
        assert time.monotonic() < deadline, "the condition never held"
        time.sleep(0.005)


@contextlib.contextmanager
def room(lead_seconds=1000):
    stream, connection = Stream(), Connection()
    speakers = []
    with contextlib.ExitStack() as patches:
        for target, name, value in (
            (mac_room_audio.mac_seat_client, "SeatStream", lambda rate: stream),
            (mac_room_audio, "open_control_connection", lambda: connection),
            (mouth_levels, "PAGE_PLAYBACK_DELAY_SECONDS", 0),
            (mac_room_audio, "LEAD_SECONDS", lead_seconds),
        ):
            patches.enter_context(patch.object(target, name, value))

        def speaker():
            speakers.append(mac_room_audio.Speaker(RATE, (LIP_SYNC_SINK,)))
            return speakers[-1]

        try:
            yield SimpleNamespace(stream=stream, connection=connection, speaker=speaker)
        finally:
            for opened in speakers:
                opened.close()
