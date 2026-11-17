import discord
from plugins.platforms.discord.adapter import VoiceReceiver

from voice_bridge.listener_stream import (
    ListenerKeyAttempt,
    rtp_synchronization_source,
)


class DecodedAudioObserver:
    def __init__(self, on_decoded):
        self._decoder = None
        self._on_decoded = on_decoded

    def decode(self, *arguments, **keywords):
        if self._decoder is None:
            self._decoder = discord.opus.Decoder()
        pcm = self._decoder.decode(*arguments, **keywords)
        self._on_decoded(pcm)
        return pcm


class ListenerVoiceReceiver(VoiceReceiver):
    def __init__(self, voice_client, listener_user_id, listener_audio):
        super().__init__(voice_client, allowed_user_ids={str(listener_user_id)})
        self._listener_user_id = listener_user_id
        self._listener_audio = listener_audio
        self._latest_decoded_pcm = None
        self.listener_packet_count = 0

    def _on_packet(self, data):
        source = rtp_synchronization_source(data)
        if source is None or source == self._bot_ssrc:
            return
        self._resolve_credentials(self._vc._connection)
        self._route_packet(source, data)

    def _route_packet(self, source, data):
        with self._lock:
            source_owner = self._ssrc_to_user.get(source)
        if source_owner == self._listener_user_id:
            self.listener_packet_count += 1
            self._decode_listener_packet(source, data)
        elif source_owner is None and self._dave_session is not None:
            self._attribute_source(source, data)

    def _attribute_source(self, source, data):
        attempt = ListenerKeyAttempt(self._dave_session, self._listener_user_id)
        secret_key, _, protocol_version, downgraded = self._creds
        self._creds = (secret_key, attempt, protocol_version, downgraded)
        self.map_ssrc(source, self._listener_user_id)
        self._decode_listener_packet(source, data)
        if attempt.opened:
            self.listener_packet_count += 1
            return
        with self._lock:
            self._ssrc_to_user.pop(source, None)
        self._decoders.pop(source, None)

    def _decode_listener_packet(self, source, data):
        if source not in self._decoders:
            self._decoders[source] = DecodedAudioObserver(self._remember_decoded_pcm)
        self._latest_decoded_pcm = None
        super()._on_packet(data)
        self._discard_buffered_audio(source)
        if self._latest_decoded_pcm is not None:
            self._listener_audio.append_discord_pcm(self._latest_decoded_pcm)

    def _remember_decoded_pcm(self, pcm):
        self._latest_decoded_pcm = pcm

    def _discard_buffered_audio(self, source):
        with self._lock:
            self._buffers.pop(source, None)
            self._last_packet_time.pop(source, None)
