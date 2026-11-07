import subprocess
import sys
import queue

import speech_segmenter
from turn_detector import TurnTracker

FRAME_BYTES = int(speech_segmenter.SAMPLE_RATE * speech_segmenter.FRAME_SECONDS) * 2
CAPTURE_RETRY_SECONDS = 1
BARGE_IN_SECONDS = 0.6


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


class SourceSpeech:
    def __init__(self, source, listening):
        self.source = source
        self.listening = listening
        self.segmenter = speech_segmenter.SpeechSegmenter()
        self.turn = TurnTracker(listening.turn_finished)
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
        if segment is None:
            self.listening.pending.finish()
            return
        turn_finished = self.turn.add(segment)
        if not enqueue_segment(
            self.listening.segments, self.source, segment, turn_finished
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


def enqueue_segment(segments, source, segment, turn_finished):
    try:
        segments.put_nowait((source, segment, turn_finished))
        return True
    except queue.Full:
        print(f"Dropped a {source} segment: transcription is behind", file=sys.stderr)
        return False
