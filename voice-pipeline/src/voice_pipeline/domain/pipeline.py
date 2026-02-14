import asyncio
import logging
from time import time

from voice_pipeline.domain.state import PipelineState, validate_transition
from voice_pipeline.domain.events import (
    BargeIn,
    ConversationWindowExpired,
    WakeWordDetected,
)
from voice_pipeline.domain.conversation import ConversationHistory
from voice_pipeline.domain.wake_word import WakeWordDetector
from voice_pipeline.ports.audio import AudioCapturePort, AudioPlaybackPort
from voice_pipeline.ports.vad import VadPort
from voice_pipeline.ports.transcriber import TranscriberPort, TranscriptEvent
from voice_pipeline.ports.completion import CompletionPort
from voice_pipeline.ports.synthesizer import SynthesizerPort

logger = logging.getLogger(__name__)

VOICE_SYSTEM_PROMPT = (
    "You are a voice assistant. Respond concisely for TTS playback, max 3 sentences. "
    "Match the spoken language (English or Portuguese). "
    "Never include file paths, code blocks, URLs, or technical formatting."
)


class VoicePipeline:
    def __init__(
        self,
        capture: AudioCapturePort,
        playback: AudioPlaybackPort,
        vad: VadPort,
        transcriber: TranscriberPort,
        completion: CompletionPort,
        synthesizer: SynthesizerPort,
        wake_word_detector: WakeWordDetector,
        conversation: ConversationHistory,
        default_agent: str = "jarvis",
        vad_threshold: float = 0.5,
        vad_min_silence_ms: int = 300,
        conversation_window_seconds: float = 15.0,
        barge_in_enabled: bool = True,
        agent_voice_map: dict[str, str] | None = None,
    ) -> None:
        self._capture = capture
        self._playback = playback
        self._vad = vad
        self._transcriber = transcriber
        self._completion = completion
        self._synthesizer = synthesizer
        self._wake_word_detector = wake_word_detector
        self._conversation = conversation

        self._agent = default_agent
        self._vad_threshold = vad_threshold
        self._vad_min_silence_ms = vad_min_silence_ms
        self._conversation_window_seconds = conversation_window_seconds
        self._barge_in_enabled = barge_in_enabled
        self._agent_voice_map = agent_voice_map or {}

        self._state = PipelineState.AMBIENT
        self._enabled = True
        self._running = False
        self._utterance_buffer: list[str] = []
        self._spoken_text_buffer: str = ""
        self._speech_active = False
        self._silence_frames = 0
        self._conversation_window_task: asyncio.Task | None = None
        self._current_tasks: list[asyncio.Task] = []

    @property
    def state(self) -> PipelineState:
        return self._state

    @property
    def agent(self) -> str:
        return self._agent

    @property
    def enabled(self) -> bool:
        return self._enabled

    def _transition_to(self, target: PipelineState) -> None:
        validate_transition(self._state, target)
        logger.info("State: %s -> %s", self._state.name, target.name)
        self._state = target

    def toggle(self) -> bool:
        self._enabled = not self._enabled
        logger.info("Pipeline %s", "enabled" if self._enabled else "disabled")
        if not self._enabled:
            self._reset_to_ambient()
        return self._enabled

    def switch_agent(self, agent: str) -> None:
        self._agent = agent
        self._conversation.clear()
        logger.info("Switched to agent: %s", agent)

    def _get_voice(self) -> str:
        return self._agent_voice_map.get(self._agent, "onyx")

    async def run(self) -> None:
        self._running = True
        logger.info("Voice pipeline started (agent=%s)", self._agent)

        await self._capture.start()
        await self._playback.start()

        try:
            audio_task = asyncio.create_task(self._audio_loop())
            transcript_task = asyncio.create_task(self._transcript_loop())
            self._current_tasks = [audio_task, transcript_task]
            await asyncio.gather(audio_task, transcript_task)
        except asyncio.CancelledError:
            logger.info("Pipeline cancelled")
        finally:
            self._running = False
            await self._cleanup()

    async def stop(self) -> None:
        self._running = False
        for task in self._current_tasks:
            task.cancel()
        await self._cleanup()

    async def _cleanup(self) -> None:
        await self._transcriber.close_session()
        await self._capture.stop()
        await self._playback.stop()

    async def _audio_loop(self) -> None:
        silence_frames_for_min_silence = int(
            self._vad_min_silence_ms / (self._capture.frame_size / self._capture.sample_rate * 1000)
        )
        stt_session_active = False

        async for frame in self._capture.read_frames():
            if not self._running or not self._enabled:
                if stt_session_active:
                    await self._transcriber.close_session()
                    stt_session_active = False
                continue

            speech_probability = self._vad.process_frame(frame)
            is_speech = speech_probability >= self._vad_threshold

            if is_speech:
                self._silence_frames = 0

                if not self._speech_active:
                    self._speech_active = True
                    logger.debug("Speech detected (prob=%.2f)", speech_probability)

                if self._state == PipelineState.SPEAKING and self._barge_in_enabled:
                    await self._handle_barge_in()

                if not stt_session_active and self._state in (
                    PipelineState.AMBIENT,
                    PipelineState.LISTENING,
                    PipelineState.CONVERSING,
                ):
                    await self._transcriber.start_session()
                    stt_session_active = True

                if stt_session_active:
                    await self._transcriber.send_audio(frame)
            else:
                self._silence_frames += 1
                if self._speech_active and self._silence_frames >= silence_frames_for_min_silence:
                    self._speech_active = False
                    logger.debug("Speech ended (silence frames=%d)", self._silence_frames)

                if stt_session_active:
                    await self._transcriber.send_audio(frame)

    async def _transcript_loop(self) -> None:
        async for event in self._transcriber.get_transcripts():
            if not self._running or not self._enabled:
                continue
            await self._handle_transcript(event)

    async def _handle_transcript(self, event: TranscriptEvent) -> None:
        if not event.text.strip():
            return

        logger.debug("Transcript (final=%s): %s", event.is_final, event.text)

        if self._state == PipelineState.AMBIENT:
            detected_word = self._wake_word_detector.detect(event.text)
            if detected_word:
                logger.info("Wake word detected: '%s' in '%s'", detected_word, event.text)
                post_wake_text = self._wake_word_detector.extract_post_wake_word_text(event.text)
                self._transition_to(PipelineState.LISTENING)
                self._utterance_buffer = [post_wake_text] if post_wake_text else []

                if event.is_final and post_wake_text:
                    await self._process_utterance()

        elif self._state == PipelineState.LISTENING:
            if event.is_final:
                self._utterance_buffer.append(event.text)
                await self._process_utterance()
            else:
                self._utterance_buffer.append(event.text)

        elif self._state == PipelineState.CONVERSING:
            self._cancel_conversation_window()
            self._transition_to(PipelineState.LISTENING)
            self._utterance_buffer = [event.text]

            if event.is_final:
                await self._process_utterance()

    async def _process_utterance(self) -> None:
        full_text = " ".join(self._utterance_buffer).strip()
        self._utterance_buffer.clear()

        if not full_text:
            self._reset_to_ambient()
            return

        logger.info("Utterance: %s", full_text)
        self._transition_to(PipelineState.THINKING)
        self._conversation.add_user_message(full_text)

        try:
            api_messages = self._conversation.to_api_messages(system_prefix=VOICE_SYSTEM_PROMPT)
            response_chunks: list[str] = []

            self._transition_to(PipelineState.SPEAKING)
            self._spoken_text_buffer = ""

            sentence_buffer = ""
            async for chunk in self._completion.stream(api_messages, self._agent):
                response_chunks.append(chunk)
                sentence_buffer += chunk

                sentence_end_index = _find_sentence_boundary(sentence_buffer)
                if sentence_end_index > 0:
                    sentence_to_speak = sentence_buffer[:sentence_end_index].strip()
                    sentence_buffer = sentence_buffer[sentence_end_index:]

                    if sentence_to_speak:
                        await self._speak_sentence(sentence_to_speak)

                if self._state != PipelineState.SPEAKING:
                    break

            if sentence_buffer.strip() and self._state == PipelineState.SPEAKING:
                await self._speak_sentence(sentence_buffer.strip())

            await self._playback.drain()
            full_response = "".join(response_chunks)
            self._conversation.add_assistant_message(full_response)
            logger.info("Response complete (%d chars)", len(full_response))

            if self._state == PipelineState.SPEAKING:
                self._transition_to(PipelineState.CONVERSING)
                self._start_conversation_window()

        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Error during completion/synthesis")
            self._reset_to_ambient()

    async def _speak_sentence(self, text: str) -> None:
        voice = self._get_voice()
        async for audio_chunk in self._synthesizer.synthesize(text, voice):
            await self._playback.play_chunk(audio_chunk)
            if self._state != PipelineState.SPEAKING:
                break
        self._spoken_text_buffer += " " + text

    async def _handle_barge_in(self) -> None:
        logger.info("Barge-in detected")
        await self._completion.cancel()
        await self._synthesizer.cancel()
        await self._playback.cancel()

        self._conversation.truncate_last_assistant_message(self._spoken_text_buffer.strip())

        self._transition_to(PipelineState.LISTENING)
        self._utterance_buffer.clear()

    def _start_conversation_window(self) -> None:
        self._cancel_conversation_window()
        self._conversation_window_task = asyncio.create_task(
            self._conversation_window_timer()
        )

    def _cancel_conversation_window(self) -> None:
        if self._conversation_window_task and not self._conversation_window_task.done():
            self._conversation_window_task.cancel()
            self._conversation_window_task = None

    async def _conversation_window_timer(self) -> None:
        try:
            await asyncio.sleep(self._conversation_window_seconds)
            if self._state == PipelineState.CONVERSING:
                logger.info("Conversation window expired")
                self._conversation.clear()
                self._transition_to(PipelineState.AMBIENT)
        except asyncio.CancelledError:
            pass

    def _reset_to_ambient(self) -> None:
        self._state = PipelineState.AMBIENT
        self._utterance_buffer.clear()
        self._speech_active = False
        self._silence_frames = 0
        self._cancel_conversation_window()


def _find_sentence_boundary(text: str) -> int:
    for i in range(len(text) - 1, -1, -1):
        if text[i] in ".!?\n" and i < len(text) - 1:
            return i + 1
    return 0
