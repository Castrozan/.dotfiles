import asyncio
import contextlib
import http.client
import json
import logging
import os
import urllib.error
import urllib.request
from collections.abc import AsyncIterator
from dataclasses import dataclass, replace
from pathlib import Path

STREAMING_SPEECH_URL = (
    "https://api.elevenlabs.io/v1/text-to-speech/{voice}/stream?output_format=pcm_48000"
)
SPEECH_MODEL = "eleven_turbo_v2_5"
SPEECH_MODELS = ("eleven_turbo_v2_5", "eleven_flash_v2_5", "eleven_multilingual_v2")
SPEECH_SAMPLE_RATE = 48000
SYNTHESIS_TIMEOUT_SECONDS = 15
API_KEY_FILE = Path.home() / ".secrets" / "elevenlabs-api-key"

logger = logging.getLogger(__name__)


class SpeechSynthesisError(Exception):
    pass


def elevenlabs_api_key():
    return os.environ.get("ELEVENLABS_API_KEY") or API_KEY_FILE.read_text().strip()


def language_code(language):
    return language.split("-")[0].lower()


def streaming_speech_request(voice, text, language, api_key, model=SPEECH_MODEL):
    if model not in SPEECH_MODELS:
        raise SpeechSynthesisError("unsupported_speech_model")
    body = {
        "text": text,
        "model_id": model,
    }
    if model != "eleven_multilingual_v2":
        body["language_code"] = language_code(language)
    return urllib.request.Request(
        STREAMING_SPEECH_URL.format(voice=voice),
        data=json.dumps(body).encode(),
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
    )


def synthesis_failure(error):
    if isinstance(error, urllib.error.HTTPError):
        return SpeechSynthesisError(f"elevenlabs_http_{error.code}")
    return SpeechSynthesisError(f"elevenlabs_unreachable_{type(error).__name__}")


class SpeechStream:
    def __init__(self, response):
        self._response = response
        self._failure = None

    def read(self, size=-1):
        try:
            return self._response.read(size)
        except (OSError, http.client.HTTPException) as error:
            logger.warning("speech stream ended early: %s", type(error).__name__)
            self._failure = SpeechSynthesisError("speech_stream_incomplete")
            return b""

    def raise_if_failed(self):
        if self._failure is not None:
            raise self._failure

    def close(self):
        self._response.close()


@dataclass(frozen=True)
class SpeechSynthesizer:
    voice: str
    model: str = SPEECH_MODEL

    @contextlib.asynccontextmanager
    async def streamed_audio(self, text, language) -> AsyncIterator[SpeechStream]:
        stream = await asyncio.to_thread(self._open_stream, text, language)
        try:
            yield stream
        finally:
            stream.close()

    def _open_stream(self, text, language):
        request = streaming_speech_request(
            self.voice, text, language, elevenlabs_api_key(), self.model
        )
        try:
            response = urllib.request.urlopen(
                request, timeout=SYNTHESIS_TIMEOUT_SECONDS
            )
        except OSError as error:
            raise synthesis_failure(error) from error
        return SpeechStream(response)


class SpeechSelection:
    def __init__(self, characters, default_voice):
        self._characters = {character["name"]: character for character in characters}
        self._character = None
        self._synthesizer = SpeechSynthesizer(default_voice)

    def capabilities(self):
        return {
            "characters": sorted(self._characters),
            "models": list(SPEECH_MODELS),
        }

    def status(self):
        return {
            "character": self._character,
            "voice": self._synthesizer.voice,
            "model": self._synthesizer.model,
        }

    def select_character(self, name):
        character = self._characters.get(name)
        if character is None:
            raise SpeechSynthesisError("unknown_character")
        self._synthesizer = replace(self._synthesizer, voice=character["cloudVoice"])
        self._character = name
        return self.status()

    def select_model(self, model):
        if model not in SPEECH_MODELS:
            raise SpeechSynthesisError("unsupported_speech_model")
        self._synthesizer = replace(self._synthesizer, model=model)
        return self.status()

    def streamed_audio(self, text, language):
        return self._synthesizer.streamed_audio(text, language)
