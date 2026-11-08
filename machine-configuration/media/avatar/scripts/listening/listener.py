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
import source_capture
import transcript_echo
import transcript_log
import turn_detector

TRANSCRIBER_RETRY_SECONDS = 1
TRANSCRIBER_ATTEMPTS = 30
PENDING_SEGMENT_LIMIT = 16
SPEECH_IN_PROGRESS_MARKER = "speech-in-progress"
EMBEDDINGS_FILE = "embeddings.jsonl"
HEARD_FILE = "heard"


def runtime_directory():
    base = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    return Path(base) / "avatar"


def every_pause_ends_the_turn(audio):
    return True


@dataclasses.dataclass
class Listening:
    segments: queue.Queue
    stopping: threading.Event
    pending: PendingSpeech
    interrupt_speaker: object
    language: str | None = None
    identify_speakers: bool = False
    turn_finished: object = every_pause_ends_the_turn


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

    def record(self, source, segment, turn_finished):
        text = transcribe_when_ready(segment, self.listening.language)
        if not text or self.echoes.is_echo(source, text, time.time()):
            return
        speaker, embedding = self.identifier.identify(segment)
        entry = transcript_log.append(
            self.path, source, text, speaker, turn_finished=turn_finished
        )
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
    try:
        while not listening.stopping.is_set():
            try:
                source, segment, turn_finished = listening.segments.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                recorder.record(source, segment, turn_finished)
            except Exception as error:
                print(f"Dropped a {source} segment: {error}", file=sys.stderr)
            finally:
                listening.pending.finish()
    finally:
        listening.pending.clear()


def interrupt_speaker():
    subprocess.Popen(
        ["avatar-command", "stop-speaking"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main():
    directory = runtime_directory()
    configuration = json.loads((directory / "listener.json").read_text())
    detector = turn_detector.SmartTurnDetector(
        os.environ[turn_detector.MODEL_ENVIRONMENT_VARIABLE]
    )
    listening = Listening(
        segments=queue.Queue(maxsize=PENDING_SEGMENT_LIMIT),
        stopping=threading.Event(),
        pending=PendingSpeech(directory / SPEECH_IN_PROGRESS_MARKER),
        interrupt_speaker=interrupt_speaker
        if configuration.get("barge_in")
        else lambda: None,
        language=configuration.get("language"),
        identify_speakers=configuration.get("identify_speakers", False),
        turn_finished=detector.finished,
    )
    signal.signal(signal.SIGTERM, lambda *_: listening.stopping.set())
    for source, device in configuration["sources"].items():
        threading.Thread(
            target=source_capture.capture_source,
            args=(source, device, listening),
            daemon=True,
        ).start()
    write_transcript(directory / "transcript.jsonl", listening)


if __name__ == "__main__":
    main()
