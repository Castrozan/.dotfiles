import asyncio
import logging
import os
import time
from collections.abc import Callable
from dataclasses import dataclass

import discord

from voice_bridge.listener_receiver import ListenerVoiceReceiver
from voice_bridge.speech_synthesis import SpeechSynthesizer

LISTEN_POLL_SECONDS = 0.05
BARGE_IN_SECONDS = 0.25
MAXIMUM_UTTERANCE_SECONDS = 30
PLAYBACK_LEAD_SILENCE_MILLISECONDS = 200

logger = logging.getLogger(__name__)


class VoiceCallError(Exception):
    pass


def exit_for_supervisor_restart_on_crash(task):
    if task.cancelled() or task.exception() is None:
        return
    logger.error("voice call task crashed", exc_info=task.exception())
    os._exit(1)


@dataclass(frozen=True)
class CallAudioServices:
    ffmpeg: str
    synthesizer: SpeechSynthesizer
    transcribe_audio: Callable[[bytes], str]


class VoiceCall:
    def __init__(self, client, listener_user_id, audio_services, feed):
        self._client = client
        self._listener_user_id = listener_user_id
        self._audio_services = audio_services
        self._feed = feed
        self._membership_lock = asyncio.Lock()
        self._speech_lock = asyncio.Lock()
        self._voice_client = None
        self._receiver = None
        self._tasks = []
        self._barged_in = False

    def status(self):
        channel = self._connected_channel()
        return {
            "joined": channel is not None,
            "channel": channel.name if channel else None,
            "guild": channel.guild.name if channel else None,
            "last_sequence": self._feed.last_sequence,
        }

    def _connected_channel(self):
        if self._voice_client is None or not self._voice_client.is_connected():
            return None
        return self._voice_client.channel

    def _listener_channel(self):
        for guild in self._client.guilds:
            for channel in guild.voice_channels:
                if self._listener_user_id in channel.voice_states:
                    return channel
        return None

    async def join(self):
        async with self._membership_lock:
            channel = self._listener_channel()
            if channel is None:
                raise VoiceCallError("listener_not_in_voice_channel")
            if self._connected_channel() == channel:
                return self.status()
            await self._disconnect()
            self._voice_client = await channel.connect()
            self._receiver = ListenerVoiceReceiver(
                self._voice_client, self._listener_user_id
            )
            self._receiver.start()
            utterances = asyncio.Queue()
            self._tasks = [
                asyncio.create_task(self._watch_listener(utterances)),
                asyncio.create_task(self._transcribe_utterances(utterances)),
            ]
            for task in self._tasks:
                task.add_done_callback(exit_for_supervisor_restart_on_crash)
            return self.status()

    async def leave(self):
        async with self._membership_lock:
            await self._disconnect()

    async def _disconnect(self):
        for task in self._tasks:
            task.cancel()
        self._tasks = []
        if self._receiver is not None:
            self._receiver.stop()
            self._receiver = None
        if self._voice_client is not None:
            await self._voice_client.disconnect()
            self._voice_client = None

    async def _watch_listener(self, utterances):
        while True:
            await asyncio.sleep(LISTEN_POLL_SECONDS)
            channel = self._connected_channel()
            if channel is not None:
                self._observe_listener(channel, utterances)

    def _observe_listener(self, channel, utterances):
        self._receiver.update_channel_occupants(
            set(channel.voice_states) - {self._client.user.id}
        )
        buffered_seconds = self._receiver.buffered_listener_seconds()
        self._stop_speaking_when_barged_in(buffered_seconds)
        for pcm in self._finished_utterances(buffered_seconds):
            utterances.put_nowait((pcm, time.time()))

    def _stop_speaking_when_barged_in(self, buffered_seconds):
        if buffered_seconds >= BARGE_IN_SECONDS and self._voice_client.is_playing():
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
                self._feed.publish(
                    text=text,
                    ended_at=ended_at,
                    transcription_seconds=round(time.monotonic() - started, 3),
                )

    async def speak(self, text, language):
        if self._connected_channel() is None:
            raise VoiceCallError("not_in_voice_channel")
        async with self._speech_lock:
            started = time.monotonic()
            async with self._audio_services.synthesizer.synthesized_audio(
                text, language
            ) as path:
                synthesis_seconds = time.monotonic() - started
                outcome = await self._play(path)
            return {
                "outcome": outcome,
                "synthesis_seconds": round(synthesis_seconds, 3),
            }

    async def _play(self, audio_path):
        voice_client = self._voice_client
        if voice_client is None or not voice_client.is_connected():
            raise VoiceCallError("not_in_voice_channel")
        if self._receiver.buffered_listener_seconds() >= BARGE_IN_SECONDS:
            return "interrupted"
        self._barged_in = False
        playback_finished = asyncio.Event()
        loop = asyncio.get_running_loop()
        voice_client.play(
            discord.FFmpegPCMAudio(
                audio_path,
                executable=self._audio_services.ffmpeg,
                options=f"-af adelay={PLAYBACK_LEAD_SILENCE_MILLISECONDS}:all=1",
            ),
            after=lambda _error: loop.call_soon_threadsafe(playback_finished.set),
        )
        await playback_finished.wait()
        return "interrupted" if self._barged_in else "finished"
