from plugins.platforms.discord.adapter import VoiceReceiver

from voice_bridge.listener_stream import (
    rtp_synchronization_source,
    source_belongs_to_listener,
)

DISCORD_PCM_BYTES_PER_SECOND = 192000


class ListenerVoiceReceiver(VoiceReceiver):
    SILENCE_THRESHOLD = 0.7
    MIN_SPEECH_DURATION = 0.3

    def __init__(self, voice_client, listener_user_id):
        super().__init__(voice_client, allowed_user_ids={str(listener_user_id)})
        self._listener_user_id = listener_user_id
        self._channel_occupants = frozenset()

    def update_channel_occupants(self, occupants):
        self._channel_occupants = frozenset(occupants)

    def buffered_listener_seconds(self):
        with self._lock:
            longest_buffer = max(map(len, self._buffers.values()), default=0)
        return longest_buffer / DISCORD_PCM_BYTES_PER_SECOND

    def _on_packet(self, data):
        source = rtp_synchronization_source(data)
        if source is None or not self._admits(source):
            return
        connection = self._vc._connection
        self._secret_key = bytes(connection.secret_key)
        self._dave_session = connection.dave_session
        super()._on_packet(data)

    def _admits(self, source):
        if source == self._bot_ssrc:
            return False
        with self._lock:
            user_by_source = dict(self._ssrc_to_user)
        admitted = source_belongs_to_listener(
            source, self._listener_user_id, user_by_source, self._channel_occupants
        )
        if admitted and source not in user_by_source:
            self.map_ssrc(source, self._listener_user_id)
        return admitted
