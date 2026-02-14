import asyncio
import io
import logging
import wave
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from voice_pipeline.ports.transcriber import TranscriptEvent

logger = logging.getLogger(__name__)


class OpenAIWhisperTranscriber:
    def __init__(self, api_key: str, sample_rate: int = 16000) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._sample_rate = sample_rate
        self._audio_buffer = bytearray()
        self._transcript_queue: asyncio.Queue[TranscriptEvent] = asyncio.Queue()
        self._session_active = False

    async def start_session(self) -> None:
        self._audio_buffer.clear()
        self._session_active = True
        logger.info("OpenAI Whisper session started")

    async def send_audio(self, frame: bytes) -> None:
        if self._session_active:
            self._audio_buffer.extend(frame)

    async def get_transcripts(self) -> AsyncIterator[TranscriptEvent]:
        while True:
            event = await self._transcript_queue.get()
            yield event

    async def close_session(self) -> None:
        if self._session_active and self._audio_buffer:
            await self._transcribe_buffer()
        self._audio_buffer.clear()
        self._session_active = False
        logger.info("OpenAI Whisper session closed")

    async def _transcribe_buffer(self) -> None:
        if not self._audio_buffer:
            return

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self._sample_rate)
            wf.writeframes(bytes(self._audio_buffer))

        wav_buffer.seek(0)
        wav_buffer.name = "audio.wav"

        try:
            result = await self._client.audio.transcriptions.create(
                model="whisper-1",
                file=wav_buffer,
                language="en",
            )
            if result.text.strip():
                event = TranscriptEvent(text=result.text.strip(), is_final=True)
                await self._transcript_queue.put(event)
        except Exception:
            logger.exception("Whisper transcription failed")
