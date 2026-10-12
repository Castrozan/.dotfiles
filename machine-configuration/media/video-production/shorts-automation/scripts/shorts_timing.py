"""Measure the edited speech stem, independently of padded music and container length."""

import array
import math
import sys
import wave

MAX_TAIL_SECONDS = 1.0
RMS_THRESHOLD = 10 ** (-45 / 20)


def audible_end(path):
    with wave.open(str(path)) as source:
        if source.getsampwidth() != 2 or source.getcomptype() != "NONE":
            raise ValueError("Retain the edited narration as 16-bit PCM WAV")
        rate, channels = source.getframerate(), source.getnchannels()
        duration = source.getnframes() / rate
        if not 0 < duration <= 180:
            raise ValueError("Narration duration must be within 180 seconds")
        return scan_voice(source, rate, channels)


def scan_voice(source, rate, channels):
    elapsed, last = 0.0, 0.0
    while raw := source.readframes(max(1, rate // 100)):
        samples = array.array("h", raw)
        if sys.byteorder != "little":
            samples.byteswap()
        elapsed += len(samples) / channels / rate
        rms = math.sqrt(sum(value * value for value in samples) / len(samples)) / 32768
        if rms >= RMS_THRESHOLD:
            last = elapsed
    if last == 0:
        raise ValueError("Narration contains no measurable speech-level signal")
    return last


def stream_end(stream):
    end = float(stream.get("start_time", 0)) + float(stream["duration"])
    if not math.isfinite(end):
        raise ValueError("Media stream end must be finite")
    return end


def validate_endings(duration, picture, audio, narration, offset):
    if abs(stream_end(picture) - stream_end(audio)) > 0.1:
        raise ValueError("Video and final audio must end within 100ms")
    if not math.isfinite(offset) or offset < 0:
        raise ValueError("Narration start must be a finite nonnegative time")
    voice_end = audible_end(narration) + offset
    tail = round(duration - voice_end, 9)
    if not -0.05 <= tail <= MAX_TAIL_SECONDS:
        raise ValueError(
            f"Final video trails edited narration by {tail:.3f}s; "
            "preserve the full speech and end within 1s"
        )
    return {
        "audible_narration_end_seconds": round(voice_end, 3),
        "tail_seconds": round(tail, 3),
        "threshold_dbfs": -45,
        "measurement_window_ms": 10,
    }
