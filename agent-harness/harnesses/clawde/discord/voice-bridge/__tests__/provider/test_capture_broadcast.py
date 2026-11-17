import asyncio
import struct

import pytest

from voice_provider.capture_broadcast import (
    MAXIMUM_LAG_SECONDS,
    SUBSCRIBER_QUEUE_FRAMES,
    CaptureBroadcast,
)
from voice_provider.listener_audio_tap import (
    CAPTURE_FRAME_BYTES,
    CAPTURE_FRAME_SECONDS,
    MAXIMUM_BACKLOG_FRAMES,
    SILENCE_FRAME,
    ListenerAudioTap,
)

DISCORD_FRAME_FRAMES = 960


class FakeTime:
    def __init__(self):
        self.now = 1000.0
        self.sleeps = []

    def clock(self):
        return self.now

    async def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds
        await asyncio.sleep(0)


class CountingTap:
    def __init__(self):
        self.taken = 0

    def take_frame(self):
        self.taken += 1
        return struct.pack("<H", self.taken) * (CAPTURE_FRAME_BYTES // 2)

    def clear(self):
        pass


def discord_frame(level):
    return struct.pack("<hh", level, level) * DISCORD_FRAME_FRAMES


async def next_frames(subscriber, count):
    return [await asyncio.wait_for(subscriber.get(), 1) for _ in range(count)]


def run(coroutine):
    return asyncio.run(coroutine)


def test_silence_frames_are_paced_in_real_time_when_no_packets_arrive():
    async def scenario():
        fake_time = FakeTime()
        broadcast = CaptureBroadcast(
            ListenerAudioTap(), fake_time.clock, fake_time.sleep
        )
        subscriber = broadcast.subscribe()
        frames = await next_frames(subscriber, 50)
        broadcast.unsubscribe(subscriber)
        assert frames == [SILENCE_FRAME] * 50
        assert all(len(frame) == 640 for frame in frames)
        assert sum(fake_time.sleeps[:49]) == pytest.approx(49 * CAPTURE_FRAME_SECONDS)

    run(scenario())


def test_listener_frames_replace_silence_when_packets_arrive():
    async def scenario():
        fake_time = FakeTime()
        tap = ListenerAudioTap()
        broadcast = CaptureBroadcast(tap, fake_time.clock, fake_time.sleep)
        subscriber = broadcast.subscribe()
        tap.append_discord_pcm(discord_frame(3000))
        tap.append_discord_pcm(discord_frame(3000))
        frames = await next_frames(subscriber, 4)
        broadcast.unsubscribe(subscriber)
        speech = struct.pack("<h", 3000) * (CAPTURE_FRAME_BYTES // 2)
        assert frames[:2] == [speech, speech]
        assert frames[2:] == [SILENCE_FRAME, SILENCE_FRAME]

    run(scenario())


def test_every_client_receives_the_same_frames():
    async def scenario():
        fake_time = FakeTime()
        tap = ListenerAudioTap()
        broadcast = CaptureBroadcast(tap, fake_time.clock, fake_time.sleep)
        first, second = broadcast.subscribe(), broadcast.subscribe()
        tap.append_discord_pcm(discord_frame(-700))
        assert await next_frames(first, 5) == await next_frames(second, 5)
        broadcast.unsubscribe(first)
        broadcast.unsubscribe(second)

    run(scenario())


def test_a_client_that_never_reads_is_dropped_from_without_blocking_the_others():
    async def scenario():
        fake_time = FakeTime()
        tap = CountingTap()
        broadcast = CaptureBroadcast(tap, fake_time.clock, fake_time.sleep)
        slow, fast = broadcast.subscribe(), broadcast.subscribe()
        frames_sent = SUBSCRIBER_QUEUE_FRAMES * 3
        received = await next_frames(fast, frames_sent)
        assert tap.taken >= frames_sent
        assert len(received) == frames_sent
        assert slow.qsize() == SUBSCRIBER_QUEUE_FRAMES
        counters = [
            struct.unpack("<H", (await slow.get())[:2])[0]
            for _ in range(SUBSCRIBER_QUEUE_FRAMES)
        ]
        assert counters == list(range(counters[0], counters[0] + len(counters)))
        assert counters[0] > 1
        broadcast.unsubscribe(slow)
        broadcast.unsubscribe(fast)

    run(scenario())


def test_pacing_stops_when_the_last_client_leaves():
    async def scenario():
        fake_time = FakeTime()
        tap = CountingTap()
        broadcast = CaptureBroadcast(tap, fake_time.clock, fake_time.sleep)
        subscriber = broadcast.subscribe()
        await next_frames(subscriber, 3)
        broadcast.unsubscribe(subscriber)
        taken = tap.taken
        for _ in range(10):
            await asyncio.sleep(0)
        assert tap.taken == taken

    run(scenario())


def test_a_stalled_loop_resumes_real_time_pacing_without_a_burst():
    async def scenario():
        fake_time = FakeTime()
        tap = CountingTap()
        original_take = tap.take_frame

        def stalling_take():
            if tap.taken == 2:
                fake_time.now += MAXIMUM_LAG_SECONDS * 4
            return original_take()

        tap.take_frame = stalling_take
        broadcast = CaptureBroadcast(tap, fake_time.clock, fake_time.sleep)
        subscriber = broadcast.subscribe()
        await next_frames(subscriber, 8)
        broadcast.unsubscribe(subscriber)
        assert fake_time.sleeps.count(0.0) <= 1

    run(scenario())


def test_the_backlog_is_bounded_to_keep_latency_low():
    tap = ListenerAudioTap()
    for _ in range(MAXIMUM_BACKLOG_FRAMES * 3):
        tap.append_discord_pcm(discord_frame(1))
    taken = 0
    while tap.take_frame() != SILENCE_FRAME:
        taken += 1
    assert taken == MAXIMUM_BACKLOG_FRAMES
