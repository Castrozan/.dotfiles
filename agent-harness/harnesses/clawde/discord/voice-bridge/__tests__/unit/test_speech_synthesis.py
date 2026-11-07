import asyncio
import io
import json
import urllib.error

import pytest

from voice_bridge import speech_synthesis


def test_the_request_streams_raw_flash_speech_in_the_spoken_language():
    request = speech_synthesis.streaming_speech_request(
        "voice-id", "Oi, Lucas.", "pt-br", "key"
    )
    assert request.full_url == (
        "https://api.elevenlabs.io/v1/text-to-speech/voice-id/stream"
        "?output_format=pcm_48000"
    )
    assert json.loads(request.data) == {
        "text": "Oi, Lucas.",
        "model_id": "eleven_flash_v2_5",
        "language_code": "pt",
    }
    assert request.get_header("Xi-api-key") == "key"


def test_the_stream_is_closed_after_playback(monkeypatch):
    stream = io.BytesIO(b"\x00\x00" * 480)
    monkeypatch.setattr(speech_synthesis, "elevenlabs_api_key", lambda: "key")
    monkeypatch.setattr(
        speech_synthesis.urllib.request, "urlopen", lambda request, timeout: stream
    )
    synthesizer = speech_synthesis.SpeechSynthesizer("voice-id")

    async def play():
        async with synthesizer.streamed_audio("Oi", "pt-br") as audio:
            return audio.read()

    assert asyncio.run(play()) == b"\x00\x00" * 480
    assert stream.closed


@pytest.mark.parametrize(
    ("error", "category"),
    [
        (
            urllib.error.HTTPError("url", 401, "Unauthorized", None, None),
            "elevenlabs_http_401",
        ),
        (TimeoutError(), "elevenlabs_unreachable_TimeoutError"),
    ],
)
def test_a_failed_stream_names_its_cause(monkeypatch, error, category):
    def failing_open(request, timeout):
        raise error

    monkeypatch.setattr(speech_synthesis, "elevenlabs_api_key", lambda: "key")
    monkeypatch.setattr(speech_synthesis.urllib.request, "urlopen", failing_open)
    synthesizer = speech_synthesis.SpeechSynthesizer("voice-id")

    async def play():
        async with synthesizer.streamed_audio("Oi", "pt-br"):
            pass

    with pytest.raises(speech_synthesis.SpeechSynthesisError, match=category):
        asyncio.run(play())


class DroppedConnection:
    def read(self, size):
        raise TimeoutError

    def close(self):
        pass


def test_a_dropped_connection_ends_the_speech_instead_of_stalling_playback():
    assert speech_synthesis.SpeechStream(DroppedConnection()).read(8192) == b""
