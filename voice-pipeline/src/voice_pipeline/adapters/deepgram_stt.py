import asyncio
import logging
from collections.abc import AsyncIterator

from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents

from voice_pipeline.ports.transcriber import TranscriptEvent

logger = logging.getLogger(__name__)


class DeepgramStreamingTranscriber:
    def __init__(self, api_key: str, sample_rate: int = 16000) -> None:
        self._api_key = api_key
        self._sample_rate = sample_rate
        self._client: DeepgramClient | None = None
        self._connection = None
        self._transcript_queue: asyncio.Queue[TranscriptEvent] = asyncio.Queue()
        self._session_active = False

    async def start_session(self) -> None:
        if self._session_active:
            await self.close_session()

        self._client = DeepgramClient(self._api_key)
        self._connection = self._client.listen.asyncwebsocket.v("1")

        self._connection.on(LiveTranscriptionEvents.Transcript, self._on_transcript)
        self._connection.on(LiveTranscriptionEvents.Error, self._on_error)

        options = LiveOptions(
            model="nova-2",
            language="multi",
            encoding="linear16",
            sample_rate=self._sample_rate,
            channels=1,
            interim_results=True,
            utterance_end_ms="1500",
            vad_events=True,
            endpointing=300,
            smart_format=True,
        )

        started = await self._connection.start(options)
        if started:
            self._session_active = True
            logger.info("Deepgram session started")
        else:
            logger.error("Failed to start Deepgram session")

    async def send_audio(self, frame: bytes) -> None:
        if self._connection and self._session_active:
            try:
                await self._connection.send(frame)
            except Exception:
                logger.warning("Failed to send audio to Deepgram")

    async def get_transcripts(self) -> AsyncIterator[TranscriptEvent]:
        while True:
            event = await self._transcript_queue.get()
            yield event

    async def close_session(self) -> None:
        if self._connection and self._session_active:
            try:
                await self._connection.finish()
            except Exception:
                pass
        self._session_active = False
        self._connection = None
        logger.info("Deepgram session closed")

    async def _on_transcript(self, _self, result, **kwargs) -> None:
        try:
            transcript = result.channel.alternatives[0].transcript
            if not transcript:
                return

            is_final = result.is_final
            speech_final = getattr(result, "speech_final", False)

            event = TranscriptEvent(
                text=transcript,
                is_final=is_final or speech_final,
            )
            await self._transcript_queue.put(event)
        except (IndexError, AttributeError):
            pass

    async def _on_error(self, _self, error, **kwargs) -> None:
        logger.error("Deepgram error: %s", error)
