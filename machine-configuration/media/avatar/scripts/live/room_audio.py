import asyncio
import queue
import subprocess
import threading

SAMPLE_WIDTH_BYTES = 2
CHUNK_SECONDS = 0.1
PLAYBACK_LATENCY_MILLISECONDS = 80
QUEUE_POLL_SECONDS = 0.25
ROOM_MICROPHONE = "AvatarRoomMicrophone"
LIP_SYNC_SINK = "AvatarLipSync"


def playback(rate, device, client):
    return subprocess.Popen(
        [
            "pacat",
            "--playback",
            "--raw",
            f"--rate={rate}",
            "--channels=1",
            "--format=s16le",
            f"--latency-msec={PLAYBACK_LATENCY_MILLISECONDS}",
            f"--client-name={client}",
            *([f"--device={device}"] if device else []),
        ],
        stdin=subprocess.PIPE,
    )


class Speaker:
    def __init__(self, rate):
        self.pending = queue.Queue()
        self.outputs = [
            playback(rate, None, "avatar-live"),
            playback(rate, LIP_SYNC_SINK, "avatar-live-lip-sync"),
        ]
        self.chunk_bytes = int(rate * CHUNK_SECONDS) * SAMPLE_WIDTH_BYTES
        self.failure = None
        threading.Thread(target=self.feed, daemon=True).start()

    def play(self, pcm):
        if self.failure:
            raise self.failure
        for start in range(0, len(pcm), self.chunk_bytes):
            self.pending.put(pcm[start : start + self.chunk_bytes])

    def buffered_seconds(self):
        return self.pending.qsize() * CHUNK_SECONDS

    def clear(self):
        while True:
            try:
                self.pending.get_nowait()
            except queue.Empty:
                return

    def feed(self):
        while True:
            try:
                chunk = self.pending.get(timeout=QUEUE_POLL_SECONDS)
            except queue.Empty:
                continue
            try:
                for output in self.outputs:
                    output.stdin.write(chunk)
                    output.stdin.flush()
            except BrokenPipeError as error:
                self.failure = error
                return

    def close(self):
        for output in self.outputs:
            output.terminate()


async def microphone_chunks(rate):
    recorder = await asyncio.create_subprocess_exec(
        "parec",
        f"--device={ROOM_MICROPHONE}",
        "--raw",
        f"--rate={rate}",
        "--channels=1",
        "--format=s16le",
        "--latency-msec=40",
        "--client-name=avatar-live-microphone",
        stdout=asyncio.subprocess.PIPE,
    )
    chunk_bytes = int(rate * CHUNK_SECONDS) * SAMPLE_WIDTH_BYTES
    try:
        while chunk := await recorder.stdout.readexactly(chunk_bytes):
            yield chunk
    finally:
        recorder.terminate()
        await recorder.wait()
