import asyncio
import http.client
import json

import pytest
from hypothesis import given, strategies as st

from voice_bridge.speech_synthesis import (
    SPEECH_MODEL,
    SPEECH_MODELS,
    SpeechStream,
    SpeechSelection,
    SpeechSynthesisError,
    streaming_speech_request,
)


CATALOG = [
    {"name": "First", "cloudVoice": "first-voice"},
    {"name": "Second", "cloudVoice": "second-voice"},
]


def test_selection_preserves_default_until_explicitly_changed():
    selection = SpeechSelection(CATALOG, "default-voice")
    assert selection.status() == {
        "character": None,
        "voice": "default-voice",
        "model": SPEECH_MODEL,
    }
    selection.select_character("Second")
    selection.select_model("eleven_flash_v2_5")
    assert selection.status() == {
        "character": "Second",
        "voice": "second-voice",
        "model": "eleven_flash_v2_5",
    }


@given(st.text().filter(lambda name: name not in {"First", "Second"}))
def test_unknown_character_cannot_mutate_selection(name):
    selection = SpeechSelection(CATALOG, "default-voice")
    previous = selection.status()
    with pytest.raises(SpeechSynthesisError, match="unknown_character"):
        selection.select_character(name)
    assert selection.status() == previous


@given(st.text().filter(lambda name: name not in SPEECH_MODELS))
def test_unknown_model_cannot_mutate_selection(name):
    selection = SpeechSelection(CATALOG, "default-voice")
    previous = selection.status()
    with pytest.raises(SpeechSynthesisError, match="unsupported_speech_model"):
        selection.select_model(name)
    assert selection.status() == previous


def test_every_supported_model_reaches_provider_payload():
    for model in SPEECH_MODELS:
        request = streaming_speech_request("voice", "Test", "en-us", "key", model)
        assert json.loads(request.data)["model_id"] == model


def test_stream_failure_is_not_a_successful_eof():
    class BrokenResponse:
        def read(self, size):
            raise http.client.IncompleteRead(b"partial")

    stream = SpeechStream(BrokenResponse())
    assert stream.read(8192) == b""
    with pytest.raises(SpeechSynthesisError, match="speech_stream_incomplete"):
        stream.raise_if_failed()


def test_stream_selection_is_snapshotted_before_provider_work(monkeypatch):
    opened = []

    def open_stream(synthesizer, text, language):
        opened.append((synthesizer.voice, synthesizer.model))
        return type("Stream", (), {"close": lambda self: None})()

    monkeypatch.setattr(
        "voice_bridge.speech_synthesis.SpeechSynthesizer._open_stream", open_stream
    )
    selection = SpeechSelection(CATALOG, "default-voice")

    async def exercise():
        async with selection.streamed_audio("test", "en-us"):
            selection.select_character("Second")
            selection.select_model("eleven_flash_v2_5")

    asyncio.run(exercise())
    assert opened == [("default-voice", SPEECH_MODEL)]
