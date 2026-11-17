import contextlib
import asyncio
import queue
import threading
import time

import mac_seat_client
from mouth_levels import CONNECTION_FAILURES, MouthLevels, open_control_connection
from pcm_resampler import LinearResampler

SAMPLE_WIDTH_BYTES = 2
CHUNK_SECONDS = 0.04
LEAD_SECONDS = 0.2
QUEUE_POLL_SECONDS = 0.25
SEAT_MICROPHONE_RATE = 16000
MICROPHONE_CHUNK_SECONDS = 0.1


class Speaker:
    def __init__(self, rate, sinks):
        self.pending = queue.Queue()
        self.stream = mac_seat_client.SeatStream(rate)
        self.mouth = MouthLevels(open_control_connection())
        self.chunk_bytes = int(rate * CHUNK_SECONDS) * SAMPLE_WIDTH_BYTES
        self.bytes_per_second = rate * SAMPLE_WIDTH_BYTES
        self.generation = 0
        self.playhead = 0.0
        self.sending = threading.Lock()
        self.interrupted = threading.Event()
        self.stopped = threading.Event()
        self.failure = None
        self.mouth.start()
        threading.Thread(target=self.feed, daemon=True).start()

    def play(self, pcm):
        failure = self.failure or self.mouth.failure
        if failure:
            raise failure
        for start in range(0, len(pcm), self.chunk_bytes):
            self.pending.put((self.generation, pcm[start : start + self.chunk_bytes]))

    def buffered_seconds(self):
        return self.pending.qsize() * CHUNK_SECONDS

    def clear(self):
        with self.sending:
            self.generation += 1
            self.playhead = 0.0
            self.drain()
        self.interrupted.set()
        self.stream.clear()
        self.mouth.silence()

    def drain(self):
        while True:
            try:
                self.pending.get_nowait()
            except queue.Empty:
                return

    def feed(self):
        try:
            while not self.stopped.is_set():
                try:
                    generation, chunk = self.pending.get(timeout=QUEUE_POLL_SECONDS)
                except queue.Empty:
                    continue
                self.deliver(generation, chunk)
        except CONNECTION_FAILURES as error:
            self.failure = error

    def deliver(self, generation, chunk):
        self.stream.open()
        ahead = self.playhead - time.monotonic() - LEAD_SECONDS
        self.interrupted.wait(max(0.0, ahead))
        self.interrupted.clear()
        with self.sending:
            if generation != self.generation:
                return
            heard_from = max(self.playhead, time.monotonic())
            self.playhead = heard_from + len(chunk) / self.bytes_per_second
            self.stream.send(chunk)
            self.mouth.show(chunk)

    def close(self):
        self.stopped.set()
        self.interrupted.set()
        self.mouth.close()
        self.stream.close()


async def microphone_chunks(rate, device):
    capture = await asyncio.create_subprocess_exec(
        *mac_seat_client.capture_command(device), stdout=asyncio.subprocess.PIPE
    )
    resampler = LinearResampler(SEAT_MICROPHONE_RATE, rate)
    chunk_bytes = (
        int(SEAT_MICROPHONE_RATE * MICROPHONE_CHUNK_SECONDS) * SAMPLE_WIDTH_BYTES
    )
    try:
        while chunk := await capture.stdout.readexactly(chunk_bytes):
            yield resampler.resample(chunk)
    finally:
        with contextlib.suppress(ProcessLookupError):
            capture.terminate()
        await capture.wait()
