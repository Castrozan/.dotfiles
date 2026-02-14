import asyncio
import logging
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class OpenAITtsSynthesizer:
    def __init__(self, api_key: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._cancelled = False

    async def synthesize(self, text: str, voice: str = "onyx") -> AsyncIterator[bytes]:
        self._cancelled = False

        try:
            async with self._client.audio.speech.with_streaming_response.create(
                model="tts-1",
                voice=voice,
                input=text,
                response_format="pcm",
                speed=1.0,
            ) as response:
                async for chunk in response.iter_bytes(chunk_size=4096):
                    if self._cancelled:
                        break
                    yield chunk
        except Exception:
            if not self._cancelled:
                logger.exception("TTS synthesis failed for: %s", text[:50])

    async def cancel(self) -> None:
        self._cancelled = True
