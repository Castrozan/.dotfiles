import asyncio
import logging
import time

from voice_bridge.listener_receiver import ListenerVoiceReceiver
from voice_bridge.speech_synthesis import SPEECH_SAMPLE_RATE
from voice_bridge.voice_playback import play_audio_stream
from voice_membership import CallAudioLifecycle, VoiceCallError, VoiceMembership

LISTEN_POLL_SECONDS = 0.05
BARGE_IN_SECONDS = 0.6
PLAYBACK_GRACE_SECONDS = 0.3
MAXIMUM_UTTERANCE_SECONDS = 30

logger = logging.getLogger(__name__)


class VoiceCall:
    def __init__(
        self, identities, listener_user_id, answered_guild_id, audio_services, feed
    ):
        self._listener_user_id = listener_user_id
        self._audio_services = audio_services
        self._feed = feed
        self._speech_lock = asyncio.Lock()
        self._receiver = None
        self._tasks = []
        self._recovery_tasks = set()
        self._barged_in = False
        self._playback_started_at = 0.0
        self._membership = VoiceMembership(
            identities,
            listener_user_id,
            answered_guild_id,
            CallAudioLifecycle(self._start_audio, self._stop_audio),
        )

    def status(self):
        return {
            **self._membership.status(),
            "last_sequence": self._feed.last_sequence,
            "speech": self._audio_services.synthesizer.status(),
            "listener_packets": self._receiver.listener_packet_count
            if self._receiver
            else 0,
        }

    async def follow_listener(self):
        await self._membership.follow_listener()

    def observe_bot_movement(self, identity):
        self._membership.observe_bot_movement(identity)

    async def join(self, preferred=None, follow=False, automatic=False):
        await self._membership.join(preferred, follow, automatic)
        return self.status()

    def _start_audio(self):
        self._receiver = ListenerVoiceReceiver(
            self._membership.voice_client, self._listener_user_id
        )
        self._receiver.start()
        utterances = asyncio.Queue()
        self._tasks = [
            asyncio.create_task(self._watch_listener(utterances)),
            asyncio.create_task(self._transcribe_utterances(utterances)),
        ]
        for task in self._tasks:
            task.add_done_callback(self._call_task_finished)

    def _call_task_finished(self, task):
        if task not in self._tasks or task.cancelled() or task.exception() is None:
            return
        logger.error("voice call task failed: %s", type(task.exception()).__name__)
        self._feed.publish(
            error="voice_call_task_failed", generation=self._membership.generation
        )
        recovery = asyncio.create_task(self.leave())
        self._recovery_tasks.add(recovery)
        recovery.add_done_callback(self._recovery_tasks.discard)

    async def leave(self):
        await self._membership.leave()

    def _stop_audio(self):
        for task in self._tasks:
            task.cancel()
        self._tasks = []
        if self._receiver is not None:
            self._receiver.stop()
            self._receiver = None

    async def _watch_listener(self, utterances):
        while True:
            await asyncio.sleep(LISTEN_POLL_SECONDS)
            if self._membership.channel() is not None:
                self._observe_listener(utterances)

    def _observe_listener(self, utterances):
        buffered_seconds = self._receiver.buffered_listener_seconds()
        self._stop_speaking_when_barged_in()
        for pcm in self._finished_utterances(buffered_seconds):
            utterances.put_nowait((pcm, time.time()))

    def _stop_speaking_when_barged_in(self):
        if not self._membership.voice_client.is_playing():
            return
        if time.monotonic() - self._playback_started_at < PLAYBACK_GRACE_SECONDS:
            self._receiver.forget_sustained_speech()
        elif self._receiver.sustained_speech_seconds() >= BARGE_IN_SECONDS:
            self._barged_in = True
            self._membership.voice_client.stop()

    def _finished_utterances(self, buffered_seconds):
        completed = self._receiver.check_silence()
        if buffered_seconds >= MAXIMUM_UTTERANCE_SECONDS:
            completed += self._receiver.flush_pending()
        return [pcm for _user_id, pcm in completed]

    async def _transcribe_utterances(self, utterances):
        while True:
            pcm, ended_at = await utterances.get()
            generation = self._membership.generation
            started = time.monotonic()
            try:
                text = await asyncio.to_thread(
                    self._audio_services.transcribe_audio, pcm
                )
            except Exception as error:
                logger.warning("transcription failed: %s", type(error).__name__)
                self._feed.publish(error="transcription_failed", ended_at=ended_at)
                continue
            if text:
                if generation != self._membership.generation:
                    continue
                self._feed.publish(
                    text=text,
                    generation=generation,
                    ended_at=ended_at,
                    transcription_seconds=round(time.monotonic() - started, 3),
                )

    async def speak(self, text, language, generation=None):
        if self._membership.channel() is None:
            raise VoiceCallError("not_in_voice_channel")
        expected_generation = (
            self._membership.generation if generation is None else generation
        )
        async with self._speech_lock:
            if expected_generation != self._membership.generation:
                raise VoiceCallError("stale_call_generation")
            started = time.monotonic()
            async with self._audio_services.synthesizer.streamed_audio(
                text, language
            ) as audio_stream:
                synthesis_seconds = time.monotonic() - started
                if expected_generation != self._membership.generation:
                    raise VoiceCallError("stale_call_generation")
                outcome = await self._play(audio_stream)
                audio_stream.raise_if_failed()
            return {
                "outcome": outcome,
                "synthesis_seconds": round(synthesis_seconds, 3),
            }

    def capabilities(self):
        return self._audio_services.synthesizer.capabilities()

    async def select_character(self, name):
        async with self._speech_lock:
            return self._audio_services.synthesizer.select_character(name)

    async def select_model(self, model):
        async with self._speech_lock:
            return self._audio_services.synthesizer.select_model(model)

    async def _play(self, audio_stream):
        voice_client = self._membership.voice_client
        if voice_client is None or not voice_client.is_connected():
            raise VoiceCallError("not_in_voice_channel")
        if self._receiver.sustained_speech_seconds() >= BARGE_IN_SECONDS:
            return "interrupted"
        self._barged_in = False
        self._playback_started_at = time.monotonic()
        await play_audio_stream(
            voice_client, audio_stream, SPEECH_SAMPLE_RATE, self._audio_services.ffmpeg
        )
        return "interrupted" if self._barged_in else "finished"
