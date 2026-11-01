from plugins.platforms.discord.adapter import VoiceReceiver

from voice_bridge.listener_stream import (
    ListenerKeyAttempt,
    rtp_synchronization_source,
)

DISCORD_PCM_BYTES_PER_SECOND = 192000


class ListenerVoiceReceiver(VoiceReceiver):
    SILENCE_THRESHOLD = 0.7
    MIN_SPEECH_DURATION = 0.3

    def __init__(self, voice_client, listener_user_id):
        super().__init__(voice_client, allowed_user_ids={str(listener_user_id)})
        self._listener_user_id = listener_user_id
        self.listener_packet_count = 0

    def buffered_listener_seconds(self):
        with self._lock:
            longest_buffer = max(map(len, self._buffers.values()), default=0)
        return longest_buffer / DISCORD_PCM_BYTES_PER_SECOND

    def _on_packet(self, data):
        source = rtp_synchronization_source(data)
        if source is None or source == self._bot_ssrc:
            return
        connection = self._vc._connection
        self._secret_key = bytes(connection.secret_key)
        with self._lock:
            source_owner = self._ssrc_to_user.get(source)
        if source_owner == self._listener_user_id:
            self._dave_session = connection.dave_session
            self.listener_packet_count += 1
            super()._on_packet(data)
        elif source_owner is None and connection.dave_session is not None:
            self._attribute_source(source, data, connection.dave_session)

    def _attribute_source(self, source, data, dave_session):
        attempt = ListenerKeyAttempt(dave_session, self._listener_user_id)
        self._dave_session = attempt
        self.map_ssrc(source, self._listener_user_id)
        super()._on_packet(data)
        if attempt.opened:
            self.listener_packet_count += 1
            return
        with self._lock:
            self._ssrc_to_user.pop(source, None)
