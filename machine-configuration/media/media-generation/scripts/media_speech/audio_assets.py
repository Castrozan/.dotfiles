import hashlib
import os
import wave
from dataclasses import asdict
from pathlib import Path

from media_speech.contract import SpeechError


def validate_pcm_audio(pcm_audio: bytes):
    if not pcm_audio or len(pcm_audio) % 2 or len(pcm_audio) > 24000 * 2 * 600:
        raise SpeechError("invalid_audio")


def validate_synthesized_speech(speech):
    if speech.sample_rate_hz != 24000:
        raise SpeechError("invalid_sample_rate")
    validate_pcm_audio(speech.pcm_audio)
    duration = len(speech.pcm_audio) / (speech.sample_rate_hz * 2)
    if speech.alignment is not None:
        speech.alignment.validate(duration)
    return duration


def write_speech_wave(audio_path: Path, speech):
    with audio_path.open("xb") as output:
        with wave.open(output, "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(speech.sample_rate_hz)
            audio.writeframes(speech.pcm_audio)
        output.flush()
        os.fsync(output.fileno())


def describe_audio(audio_path: Path, speech, duration: float):
    return {
        "path": str(audio_path),
        "mime_type": "audio/wav",
        "encoding": "pcm_s16le",
        "sample_rate_hz": speech.sample_rate_hz,
        "channels": 1,
        "duration_seconds": duration,
        "size_bytes": audio_path.stat().st_size,
        "sha256": hashlib.sha256(audio_path.read_bytes()).hexdigest(),
    }


def describe_alignment(alignment, text: str):
    if alignment is None:
        return {"status": "unavailable"}
    return {
        "status": "available",
        "granularity": "character",
        "text_matches_input": "".join(alignment.characters) == text,
        **asdict(alignment),
    }
