import array
import collections
import math

SAMPLE_RATE = 16000
FRAME_SECONDS = 0.03
SPEECH_LEVEL = 300
LEAD_IN_SECONDS = 0.3
TRAILING_SILENCE_SECONDS = 0.7
MINIMUM_SPEECH_SECONDS = 0.3
MAXIMUM_SEGMENT_SECONDS = 12


def frame_level(frame):
    samples = array.array("h", frame)
    if not samples:
        return 0
    return math.sqrt(sum(sample * sample for sample in samples) / len(samples))


def frames_for(seconds):
    return int(seconds / FRAME_SECONDS)


class SpeechSegmenter:
    def __init__(self):
        self.lead_in = collections.deque(maxlen=frames_for(LEAD_IN_SECONDS))
        self.segment = []
        self.speech_frames = 0
        self.silent_frames = 0

    def feed(self, frame):
        speaking = frame_level(frame) >= SPEECH_LEVEL
        if not self.segment:
            return self.wait_for_speech(frame, speaking)
        self.segment.append(frame)
        self.speech_frames += speaking
        self.silent_frames = 0 if speaking else self.silent_frames + 1
        ended = self.silent_frames >= frames_for(TRAILING_SILENCE_SECONDS)
        if ended or len(self.segment) >= frames_for(MAXIMUM_SEGMENT_SECONDS):
            return self.finish()
        return None

    def wait_for_speech(self, frame, speaking):
        if speaking:
            self.segment = [*self.lead_in, frame]
            self.lead_in.clear()
            self.speech_frames = 1
            self.silent_frames = 0
        else:
            self.lead_in.append(frame)
        return None

    def finish(self):
        segment = b"".join(self.segment)
        was_speech = self.speech_frames >= frames_for(MINIMUM_SPEECH_SECONDS)
        self.segment = []
        self.speech_frames = 0
        self.silent_frames = 0
        return segment if was_speech else None
