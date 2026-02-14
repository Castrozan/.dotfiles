import asyncio
import io
import wave
from collections.abc import AsyncIterator
from dataclasses import dataclass

import numpy as np
import pytest

from voice_pipeline.domain.conversation import ConversationHistory
from voice_pipeline.domain.wake_word import WakeWordDetector
from voice_pipeline.ports.transcriber import TranscriptEvent


SAMPLE_RATE = 16000
FRAME_DURATION_MS = 30
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)


def generate_silence(duration_ms: int = 30, sample_rate: int = SAMPLE_RATE) -> bytes:
    num_samples = int(sample_rate * duration_ms / 1000)
    return np.zeros(num_samples, dtype=np.int16).tobytes()


def generate_sine_wave(
    frequency: float = 440.0,
    duration_ms: int = 30,
    amplitude: float = 0.8,
    sample_rate: int = SAMPLE_RATE,
) -> bytes:
    num_samples = int(sample_rate * duration_ms / 1000)
    t = np.arange(num_samples) / sample_rate
    signal = np.sin(2 * np.pi * frequency * t) * amplitude
    return (signal * 32767).astype(np.int16).tobytes()


def generate_white_noise(
    duration_ms: int = 30,
    amplitude: float = 0.5,
    sample_rate: int = SAMPLE_RATE,
) -> bytes:
    num_samples = int(sample_rate * duration_ms / 1000)
    noise = np.random.uniform(-1, 1, num_samples) * amplitude
    return (noise * 32767).astype(np.int16).tobytes()


def generate_speech_like_signal(
    duration_ms: int = 1000,
    sample_rate: int = SAMPLE_RATE,
) -> bytes:
    num_samples = int(sample_rate * duration_ms / 1000)
    t = np.arange(num_samples) / sample_rate
    fundamental = np.sin(2 * np.pi * 150 * t) * 0.4
    harmonic2 = np.sin(2 * np.pi * 300 * t) * 0.2
    harmonic3 = np.sin(2 * np.pi * 450 * t) * 0.1
    noise = np.random.uniform(-1, 1, num_samples) * 0.05
    signal = fundamental + harmonic2 + harmonic3 + noise
    envelope = np.ones(num_samples)
    fade_samples = int(sample_rate * 0.01)
    envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
    envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
    signal *= envelope
    return (signal * 32767).astype(np.int16).tobytes()


def pcm_to_wav_bytes(pcm_data: bytes, sample_rate: int = SAMPLE_RATE) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return buffer.getvalue()


def split_into_frames(pcm_data: bytes, frame_size: int = FRAME_SIZE) -> list[bytes]:
    bytes_per_frame = frame_size * 2
    frames = []
    for i in range(0, len(pcm_data), bytes_per_frame):
        chunk = pcm_data[i : i + bytes_per_frame]
        if len(chunk) == bytes_per_frame:
            frames.append(chunk)
    return frames


class FakeAudioCapture:
    def __init__(self, frames: list[bytes] | None = None) -> None:
        self._frames = frames or []
        self._sample_rate = SAMPLE_RATE
        self._frame_size = FRAME_SIZE
        self._started = False

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    @property
    def frame_size(self) -> int:
        return self._frame_size

    async def start(self) -> None:
        self._started = True

    async def stop(self) -> None:
        self._started = False

    async def read_frames(self) -> AsyncIterator[bytes]:
        for frame in self._frames:
            yield frame

    def feed_frames(self, frames: list[bytes]) -> None:
        self._frames.extend(frames)


class FakeAudioPlayback:
    def __init__(self) -> None:
        self._chunks: list[bytes] = []
        self._started = False
        self._cancelled = False

    @property
    def played_chunks(self) -> list[bytes]:
        return self._chunks

    @property
    def total_bytes_played(self) -> int:
        return sum(len(c) for c in self._chunks)

    async def start(self) -> None:
        self._started = True

    async def stop(self) -> None:
        self._started = False

    async def play_chunk(self, audio_data: bytes) -> None:
        if not self._cancelled:
            self._chunks.append(audio_data)

    async def drain(self) -> None:
        pass

    async def cancel(self) -> None:
        self._cancelled = True
        self._chunks.clear()


class FakeVad:
    def __init__(self, probabilities: list[float] | None = None) -> None:
        self._probabilities = probabilities or []
        self._call_count = 0

    def process_frame(self, audio_frame: bytes) -> float:
        if self._call_count < len(self._probabilities):
            prob = self._probabilities[self._call_count]
        else:
            prob = 0.0
        self._call_count += 1
        return prob

    def reset(self) -> None:
        self._call_count = 0

    def set_probabilities(self, probabilities: list[float]) -> None:
        self._probabilities = probabilities
        self._call_count = 0


class FakeTranscriber:
    def __init__(self) -> None:
        self._events: list[TranscriptEvent] = []
        self._event_index = 0
        self._session_active = False
        self._audio_received: list[bytes] = []

    async def start_session(self) -> None:
        self._session_active = True

    async def send_audio(self, frame: bytes) -> None:
        self._audio_received.append(frame)

    async def get_transcripts(self) -> AsyncIterator[TranscriptEvent]:
        for event in self._events:
            yield event

    async def close_session(self) -> None:
        self._session_active = False

    def queue_events(self, events: list[TranscriptEvent]) -> None:
        self._events.extend(events)


class FakeCompletion:
    def __init__(self, responses: dict[str, list[str]] | None = None) -> None:
        self._responses = responses or {}
        self._default_response = ["Hello", " there!"]
        self._cancelled = False
        self._call_count = 0

    async def stream(
        self,
        messages: list[dict[str, str]],
        agent: str,
    ) -> AsyncIterator[str]:
        self._cancelled = False
        self._call_count += 1
        chunks = self._responses.get(agent, self._default_response)
        for chunk in chunks:
            if self._cancelled:
                break
            yield chunk
            await asyncio.sleep(0)

    async def cancel(self) -> None:
        self._cancelled = True


class FakeSynthesizer:
    def __init__(self, audio_chunk: bytes | None = None) -> None:
        self._audio_chunk = audio_chunk or generate_sine_wave(duration_ms=100)
        self._cancelled = False
        self._synthesize_count = 0

    async def synthesize(self, text: str, voice: str = "onyx") -> AsyncIterator[bytes]:
        self._cancelled = False
        self._synthesize_count += 1
        for _ in range(3):
            if self._cancelled:
                break
            yield self._audio_chunk
            await asyncio.sleep(0)

    async def cancel(self) -> None:
        self._cancelled = True


@pytest.fixture
def silence_frames():
    return [generate_silence() for _ in range(10)]


@pytest.fixture
def speech_frames():
    pcm = generate_speech_like_signal(duration_ms=500)
    return split_into_frames(pcm)


@pytest.fixture
def noise_frames():
    return [generate_white_noise() for _ in range(10)]


@pytest.fixture
def mixed_silence_and_speech():
    silence = [generate_silence() for _ in range(5)]
    speech = split_into_frames(generate_speech_like_signal(duration_ms=300))
    trailing_silence = [generate_silence() for _ in range(5)]
    return silence + speech + trailing_silence


@pytest.fixture
def fake_capture():
    return FakeAudioCapture()


@pytest.fixture
def fake_playback():
    return FakeAudioPlayback()


@pytest.fixture
def fake_vad():
    return FakeVad()


@pytest.fixture
def fake_transcriber():
    return FakeTranscriber()


@pytest.fixture
def fake_completion():
    return FakeCompletion()


@pytest.fixture
def fake_synthesizer():
    return FakeSynthesizer()


@pytest.fixture
def wake_word_detector():
    return WakeWordDetector(["jarvis", "robson", "jenny"])


@pytest.fixture
def conversation():
    return ConversationHistory(max_turns=20)
