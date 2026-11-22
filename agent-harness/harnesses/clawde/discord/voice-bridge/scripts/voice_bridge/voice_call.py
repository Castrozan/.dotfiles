import asyncio

from voice_bridge.listener_receiver import ListenerVoiceReceiver
from voice_bridge.voice_playback import play_audio_stream
from voice_membership import CallAudioLifecycle, VoiceCallError, VoiceMembership


class VoiceCall:
    def __init__(self, identities, listener_user_id, answered_guild_id, audio_services):
        self._listener_user_id = listener_user_id
        self._audio_services = audio_services
        self._speech_lock = asyncio.Lock()
        self._receiver = None
        self._interrupted = False
        self._membership = VoiceMembership(
            identities,
            listener_user_id,
            answered_guild_id,
            CallAudioLifecycle(self._start_audio, self._stop_audio),
        )

    def status(self):
        return {
            **self._membership.status(),
            "listener_packets": self._receiver.listener_packet_count
            if self._receiver
            else 0,
        }

    async def follow_listener(self):
        await self._membership.follow_listener()

    def observe_bot_movement(self, identity):
        self._membership.observe_bot_movement(identity)

    async def release_stale_voice_state(self, identity):
        await self._membership.release_stale_voice_state(identity)

    async def join(self, preferred=None, follow=False, automatic=False):
        await self._membership.join(preferred, follow, automatic)
        return self.status()

    def _start_audio(self):
        self._receiver = ListenerVoiceReceiver(
            self._membership.voice_client,
            self._listener_user_id,
            self._audio_services.listener_audio,
        )
        self._receiver.start()

    async def leave(self):
        await self._membership.leave()

    def _stop_audio(self):
        if self._receiver is not None:
            self._receiver.stop()
            self._receiver = None

    async def _play(self, audio_stream, sample_rate):
        voice_client = self._membership.voice_client
        if voice_client is None or not voice_client.is_connected():
            raise VoiceCallError("not_in_voice_channel")
        self._interrupted = False
        await play_audio_stream(
            voice_client, audio_stream, sample_rate, self._audio_services.ffmpeg
        )
        return "interrupted" if self._interrupted else "finished"
