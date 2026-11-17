import asyncio
import time

from voice_provider.listener_audio_tap import CAPTURE_FRAME_SECONDS

SUBSCRIBER_QUEUE_FRAMES = 100
MAXIMUM_LAG_SECONDS = 0.5


class CaptureBroadcast:
    def __init__(self, audio_tap, clock=time.monotonic, sleep=asyncio.sleep):
        self._audio_tap = audio_tap
        self._clock = clock
        self._sleep = sleep
        self._subscribers = set()
        self._pacer = None

    def subscribe(self):
        subscriber = asyncio.Queue(maxsize=SUBSCRIBER_QUEUE_FRAMES)
        if not self._subscribers:
            self._audio_tap.clear()
            self._pacer = asyncio.create_task(self._pace())
        self._subscribers.add(subscriber)
        return subscriber

    def unsubscribe(self, subscriber):
        self._subscribers.discard(subscriber)
        if not self._subscribers and self._pacer is not None:
            self._pacer.cancel()
            self._pacer = None

    async def _pace(self):
        next_frame_at = self._clock()
        while True:
            self._publish(self._audio_tap.take_frame())
            next_frame_at += CAPTURE_FRAME_SECONDS
            lag = self._clock() - next_frame_at
            if lag > MAXIMUM_LAG_SECONDS:
                next_frame_at += lag
            await self._sleep(max(0.0, next_frame_at - self._clock()))

    def _publish(self, frame):
        for subscriber in self._subscribers:
            if subscriber.full():
                subscriber.get_nowait()
            subscriber.put_nowait(frame)
