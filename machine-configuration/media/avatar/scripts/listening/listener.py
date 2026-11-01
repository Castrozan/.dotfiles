import json
import os
import queue
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import speech_segmenter
import transcriber
import transcript_log

FRAME_BYTES = int(speech_segmenter.SAMPLE_RATE * speech_segmenter.FRAME_SECONDS) * 2
CAPTURE_RETRY_SECONDS = 1
TRANSCRIBER_RETRY_SECONDS = 1
TRANSCRIBER_ATTEMPTS = 30
PENDING_SEGMENT_LIMIT = 16


def runtime_directory():
    base = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    return Path(base) / "avatar"


def capture_command(device):
    return [
        "parec",
        f"--device={device}",
        "--client-name=avatar-listener",
        "--property=node.dont-reconnect=true",
        "--property=node.dont-fallback=true",
        "--raw",
        "--format=s16le",
        f"--rate={speech_segmenter.SAMPLE_RATE}",
        "--channels=1",
        "--latency-msec=100",
    ]


def capture_source(source, device, segments, stopping):
    while not stopping.is_set():
        capture = subprocess.Popen(capture_command(device), stdout=subprocess.PIPE)
        segmenter = speech_segmenter.SpeechSegmenter()
        while not stopping.is_set() and (frame := capture.stdout.read(FRAME_BYTES)):
            if segment := segmenter.feed(frame):
                enqueue_segment(segments, source, segment)
        capture.terminate()
        capture.wait()
        stopping.wait(CAPTURE_RETRY_SECONDS)


def enqueue_segment(segments, source, segment):
    try:
        segments.put_nowait((source, segment))
    except queue.Full:
        print(f"Dropped a {source} segment: transcription is behind", file=sys.stderr)


def transcribe_when_ready(segment):
    for _ in range(TRANSCRIBER_ATTEMPTS):
        try:
            return transcriber.transcribe(segment)
        except OSError:
            time.sleep(TRANSCRIBER_RETRY_SECONDS)
    raise TimeoutError("The local transcriber did not answer")


def write_transcript(path, segments, stopping):
    while not stopping.is_set():
        try:
            source, segment = segments.get(timeout=0.5)
        except queue.Empty:
            continue
        if text := transcribe_when_ready(segment):
            transcript_log.append(path, source, text)


def main():
    directory = runtime_directory()
    sources = json.loads((directory / "listener.json").read_text())["sources"]
    stopping = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stopping.set())
    segments = queue.Queue(maxsize=PENDING_SEGMENT_LIMIT)
    for source, device in sources.items():
        threading.Thread(
            target=capture_source,
            args=(source, device, segments, stopping),
            daemon=True,
        ).start()
    write_transcript(directory / "transcript.jsonl", segments, stopping)


if __name__ == "__main__":
    main()
