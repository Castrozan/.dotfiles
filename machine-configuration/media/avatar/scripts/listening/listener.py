import dataclasses
import json
import os
import queue
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import cloud_transcriber
import speaker_identity
from pending_speech import PendingSpeech
import speech_segmenter
import transcript_echo
import transcript_log

FRAME_BYTES = int(speech_segmenter.SAMPLE_RATE * speech_segmenter.FRAME_SECONDS) * 2
CAPTURE_RETRY_SECONDS = 1
TRANSCRIBER_RETRY_SECONDS = 1
TRANSCRIBER_ATTEMPTS = 30
PENDING_SEGMENT_LIMIT = 16
BARGE_IN_SECONDS = 0.6
SPEECH_IN_PROGRESS_MARKER = "speech-in-progress"
EMBEDDINGS_FILE = "embeddings.jsonl"


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


@dataclasses.dataclass
class Listening:
    segments: queue.Queue
    stopping: threading.Event
    pending: PendingSpeech
    interrupt_speaker: object
    language: str | None = None
    identify_speakers: bool = False


class SourceSpeech:
    def __init__(self, source, listening):
        self.source = source
        self.listening = listening
        self.segmenter = speech_segmenter.SpeechSegmenter()
        self.interrupted = False

    def feed(self, frame):
        was_active = self.segmenter.active
        segment = self.segmenter.feed(frame)
        if self.segmenter.active:
            if not was_active:
                self.listening.pending.begin()
            self.interrupt_when_sustained()
        elif was_active:
            self.interrupted = False
            self.hand_over(segment)

    def interrupt_when_sustained(self):
        if (
            self.segmenter.sustained_seconds >= BARGE_IN_SECONDS
            and not self.interrupted
        ):
            self.interrupted = True
            self.listening.interrupt_speaker()

    def hand_over(self, segment):
        if segment is None or not enqueue_segment(
            self.listening.segments, self.source, segment
        ):
            self.listening.pending.finish()

    def abandon(self):
        if self.segmenter.active:
            self.listening.pending.finish()


def capture_source(source, device, listening):
    while not listening.stopping.is_set():
        capture = subprocess.Popen(capture_command(device), stdout=subprocess.PIPE)
        speech = SourceSpeech(source, listening)
        while not listening.stopping.is_set() and (
            frame := capture.stdout.read(FRAME_BYTES)
        ):
            speech.feed(frame)
        speech.abandon()
        capture.terminate()
        capture.wait()
        listening.stopping.wait(CAPTURE_RETRY_SECONDS)


def enqueue_segment(segments, source, segment):
    try:
        segments.put_nowait((source, segment))
        return True
    except queue.Full:
        print(f"Dropped a {source} segment: transcription is behind", file=sys.stderr)
        return False


def transcribe_when_ready(segment, language):
    for _ in range(TRANSCRIBER_ATTEMPTS):
        try:
            return cloud_transcriber.transcribe_with_local_fallback(segment, language)
        except OSError:
            time.sleep(TRANSCRIBER_RETRY_SECONDS)
    raise TimeoutError("No transcriber answered")


@dataclasses.dataclass
class TranscriptRecorder:
    path: Path
    listening: Listening
    echoes: transcript_echo.EchoFilter
    identifier: object

    def record(self, source, segment):
        text = transcribe_when_ready(segment, self.listening.language)
        if not text or self.echoes.is_echo(source, text, time.time()):
            return
        speaker, embedding = self.identifier.identify(segment)
        entry = transcript_log.append(self.path, source, text, speaker)
        if embedding:
            speaker_identity.append_embedding(
                self.path.with_name(EMBEDDINGS_FILE), entry["sequence"], embedding
            )


def write_transcript(path, listening):
    recorder = TranscriptRecorder(
        path,
        listening,
        transcript_echo.EchoFilter(),
        speaker_identity.configured_identifier(listening.identify_speakers),
    )
    while not listening.stopping.is_set():
        try:
            source, segment = listening.segments.get(timeout=0.5)
        except queue.Empty:
            continue
        try:
            recorder.record(source, segment)
        finally:
            listening.pending.finish()


def interrupt_speaker():
    subprocess.Popen(
        ["avatar-command", "stop-speaking"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main():
    directory = runtime_directory()
    configuration = json.loads((directory / "listener.json").read_text())
    listening = Listening(
        segments=queue.Queue(maxsize=PENDING_SEGMENT_LIMIT),
        stopping=threading.Event(),
        pending=PendingSpeech(directory / SPEECH_IN_PROGRESS_MARKER),
        interrupt_speaker=interrupt_speaker
        if configuration.get("barge_in")
        else lambda: None,
        language=configuration.get("language"),
        identify_speakers=configuration.get("identify_speakers", False),
    )
    signal.signal(signal.SIGTERM, lambda *_: listening.stopping.set())
    for source, device in configuration["sources"].items():
        threading.Thread(
            target=capture_source,
            args=(source, device, listening),
            daemon=True,
        ).start()
    write_transcript(directory / "transcript.jsonl", listening)


if __name__ == "__main__":
    main()
