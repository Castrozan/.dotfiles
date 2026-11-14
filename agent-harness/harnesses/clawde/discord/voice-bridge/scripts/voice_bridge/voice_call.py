import asyncio
import logging
import time
import uuid

from voice_bridge.listener_receiver import ListenerVoiceReceiver
from voice_bridge.speech_synthesis import SPEECH_SAMPLE_RATE
from voice_bridge.voice_playback import play_audio_stream
from voice_identity import channel_refusal

LISTEN_POLL_SECONDS = 0.05
BARGE_IN_SECONDS = 0.6
PLAYBACK_GRACE_SECONDS = 0.3
MAXIMUM_UTTERANCE_SECONDS = 30

logger = logging.getLogger(__name__)


class VoiceCallError(Exception):
    pass




class VoiceCall:
    def __init__(
        self, identities, listener_user_id, answered_guild_id, audio_services, feed
    ):
        self._identities = identities
        self._identity = None
        self._listener_user_id = listener_user_id
        self._answered_guild_id = answered_guild_id
        self._audio_services = audio_services
        self._feed = feed
        self._membership_lock = asyncio.Lock()
        self._speech_lock = asyncio.Lock()
        self._voice_client = None
        self._receiver = None
        self._tasks = []
        self._barged_in = False
        self._playback_started_at = 0.0
        self._following = False
        self._generation = uuid.uuid4().hex

    def status(self):
        channel = self._connected_channel()
        return {
            "joined": channel is not None,
            "generation": self._generation,
            "following": self._following,
            "bot": self._identity.name if self._identity else None,
            "identities": self._identities.status(
                self._listener_user_id, self._answered_guild_id
            ),
            "channel_id": str(channel.id) if channel else None,
            "guild_id": str(channel.guild.id) if channel else None,
            "channel": channel.name if channel else None,
            "guild": channel.guild.name if channel else None,
            "last_sequence": self._feed.last_sequence,
            "speech": self._audio_services.synthesizer.status(),
            "listener_packets": self._receiver.listener_packet_count
            if self._receiver
            else 0,
        }

    def _connected_channel(self):
        if self._voice_client is None or not self._voice_client.is_connected():
            return None
        return self._voice_client.channel

    def _listener_channel(self):
        if self._identity is None:
            return None
        guild = self._identity.client.get_guild(self._answered_guild_id)
        if guild is not None:
            for channel in guild.voice_channels:
                if self._listener_user_id in channel.voice_states:
                    return channel
        return None

    async def follow_listener(self):
        if not self._following:
            return
        channel = self._listener_channel()
        if self._identity is None:
            if (
                next(
                    self._identities.candidates(
                        self._listener_user_id, self._answered_guild_id
                    ),
                    None,
                )
                is not None
            ):
                await self.join(follow=True, automatic=True)
            return
        if channel is not None and channel.guild.id == self._answered_guild_id:
            await self.join(follow=True, automatic=True)
        elif self._connected_channel() != channel:
            async with self._membership_lock:
                await self._disconnect()

    def observe_bot_movement(self, identity):
        if identity is self._identity:
            self._generation = uuid.uuid4().hex
            if self._voice_client is not None:
                self._voice_client.stop()

    async def join(self, preferred=None, follow=False, automatic=False):
        async with self._membership_lock:
            if automatic and not self._following:
                return self.status()
            channel = self._listener_channel()
            if channel is not None and self._connected_channel() == channel:
                self._following = follow
                return self.status()
            await self._disconnect()
            for identity, channel in self._identities.candidates(
                self._listener_user_id, self._answered_guild_id, preferred
            ):
                if not self._identities.reserve(identity):
                    continue
                member = channel.guild.me
                if (
                    member.voice and member.voice.channel is not None
                ) or channel_refusal(channel, member):
                    self._identities.release(identity)
                    continue
                try:
                    self._voice_client = await channel.connect(
                        timeout=20, reconnect=True
                    )
                except BaseException as error:
                    self._identities.release(identity)
                    if not isinstance(error, Exception):
                        raise
                    logger.warning(
                        "voice identity %s join failed: %s",
                        identity.name,
                        type(error).__name__,
                    )
                    continue
                self._identity = identity
                break
            if self._identity is None:
                raise VoiceCallError("no_eligible_available_bot_for_listener")
            self._following = follow
            try:
                self._receiver = ListenerVoiceReceiver(
                    self._voice_client, self._listener_user_id
                )
                self._receiver.start()
            except BaseException:
                await self._disconnect()
                raise
            utterances = asyncio.Queue()
            self._tasks = [
                asyncio.create_task(self._watch_listener(utterances)),
                asyncio.create_task(self._transcribe_utterances(utterances)),
            ]
            for task in self._tasks:
                task.add_done_callback(self._call_task_finished)
            return self.status()

    def _call_task_finished(self, task):
        if task not in self._tasks or task.cancelled() or task.exception() is None:
            return
        logger.error("voice call task failed: %s", type(task.exception()).__name__)
        self._feed.publish(error="voice_call_task_failed", generation=self._generation)
        asyncio.create_task(self.leave())

    async def leave(self):
        async with self._membership_lock:
            self._following = False
            await self._disconnect()

    async def _disconnect(self):
        self._generation = uuid.uuid4().hex
        for task in self._tasks:
            task.cancel()
        self._tasks = []
        if self._receiver is not None:
            self._receiver.stop()
            self._receiver = None
        if self._voice_client is not None:
            self._voice_client.stop()
            await self._voice_client.disconnect()
            self._voice_client = None
        if self._identity is not None:
            self._identities.release(self._identity)
            self._identity = None

    async def _watch_listener(self, utterances):
        while True:
            await asyncio.sleep(LISTEN_POLL_SECONDS)
            if self._connected_channel() is not None:
                self._observe_listener(utterances)

    def _observe_listener(self, utterances):
        buffered_seconds = self._receiver.buffered_listener_seconds()
        self._stop_speaking_when_barged_in()
        for pcm in self._finished_utterances(buffered_seconds):
            utterances.put_nowait((pcm, time.time()))

    def _stop_speaking_when_barged_in(self):
        if not self._voice_client.is_playing():
            return
        if time.monotonic() - self._playback_started_at < PLAYBACK_GRACE_SECONDS:
            self._receiver.forget_sustained_speech()
        elif self._receiver.sustained_speech_seconds() >= BARGE_IN_SECONDS:
            self._barged_in = True
            self._voice_client.stop()

    def _finished_utterances(self, buffered_seconds):
        completed = self._receiver.check_silence()
        if buffered_seconds >= MAXIMUM_UTTERANCE_SECONDS:
            completed += self._receiver.flush_pending()
        return [pcm for _user_id, pcm in completed]

    async def _transcribe_utterances(self, utterances):
        while True:
            pcm, ended_at = await utterances.get()
            generation = self._generation
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
                if generation != self._generation:
                    continue
                self._feed.publish(
                    text=text,
                    generation=generation,
                    ended_at=ended_at,
                    transcription_seconds=round(time.monotonic() - started, 3),
                )

    async def speak(self, text, language, generation=None):
        if self._connected_channel() is None:
            raise VoiceCallError("not_in_voice_channel")
        expected_generation = self._generation if generation is None else generation
        async with self._speech_lock:
            if expected_generation != self._generation:
                raise VoiceCallError("stale_call_generation")
            started = time.monotonic()
            async with self._audio_services.synthesizer.streamed_audio(
                text, language
            ) as audio_stream:
                synthesis_seconds = time.monotonic() - started
                if expected_generation != self._generation:
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
        voice_client = self._voice_client
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
