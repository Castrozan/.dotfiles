import asyncio
import contextlib
import json
import os
import urllib.error
import urllib.request
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

STREAMING_SPEECH_URL = (
    "https://api.elevenlabs.io/v1/text-to-speech/{voice}/stream?output_format=pcm_48000"
)
SPEECH_MODEL = "eleven_flash_v2_5"
SPEECH_SAMPLE_RATE = 48000
SYNTHESIS_TIMEOUT_SECONDS = 15
API_KEY_FILE = Path.home() / ".secrets" / "elevenlabs-api-key"


class SpeechSynthesisError(Exception):
    pass


def elevenlabs_api_key():
    return os.environ.get("ELEVENLABS_API_KEY") or API_KEY_FILE.read_text().strip()


def language_code(language):
    return language.split("-")[0].lower()


def streaming_speech_request(voice, text, language, api_key):
    body = {
        "text": text,
        "model_id": SPEECH_MODEL,
        "language_code": language_code(language),
    }
    return urllib.request.Request(
        STREAMING_SPEECH_URL.format(voice=voice),
        data=json.dumps(body).encode(),
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
    )


def synthesis_failure(error):
    if isinstance(error, urllib.error.HTTPError):
        return SpeechSynthesisError(f"elevenlabs_http_{error.code}")
    return SpeechSynthesisError(f"elevenlabs_unreachable_{type(error).__name__}")


@dataclass(frozen=True)
class SpeechSynthesizer:
    voice: str

    @contextlib.asynccontextmanager
    async def streamed_audio(self, text, language) -> AsyncIterator[BinaryIO]:
        stream = await asyncio.to_thread(self._open_stream, text, language)
        try:
            yield stream
        finally:
            stream.close()

    def _open_stream(self, text, language):
        request = streaming_speech_request(
            self.voice, text, language, elevenlabs_api_key()
        )
        try:
            return urllib.request.urlopen(request, timeout=SYNTHESIS_TIMEOUT_SECONDS)
        except OSError as error:
            raise synthesis_failure(error) from error
