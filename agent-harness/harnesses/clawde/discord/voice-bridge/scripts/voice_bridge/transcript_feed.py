import asyncio
from collections import deque

RETAINED_LINE_COUNT = 64


class TranscriptFeed:
    def __init__(self):
        self._retained_lines = deque(maxlen=RETAINED_LINE_COUNT)
        self._subscribers = set()
        self._last_sequence = 0

    @property
    def last_sequence(self):
        return self._last_sequence

    def publish(self, **fields):
        self._last_sequence += 1
        line = {"sequence": self._last_sequence, **fields}
        self._retained_lines.append(line)
        for subscriber in self._subscribers:
            subscriber.put_nowait(line)

    def subscribe(self, after_sequence):
        subscriber = asyncio.Queue()
        for line in self._retained_lines:
            if line["sequence"] > after_sequence:
                subscriber.put_nowait(line)
        self._subscribers.add(subscriber)
        return subscriber

    def unsubscribe(self, subscriber):
        self._subscribers.discard(subscriber)
