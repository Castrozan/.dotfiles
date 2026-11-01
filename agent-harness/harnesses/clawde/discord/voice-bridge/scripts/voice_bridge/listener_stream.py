RTP_HEADER_BYTES = 12
RTP_SYNCHRONIZATION_SOURCE_OFFSET = 8
RTP_VERSION = 2
DISCORD_VOICE_PAYLOAD_TYPE = 0x78
DAVE_FRAME_MARKER = b"\xfa\xfa"


def rtp_synchronization_source(packet):
    if len(packet) < RTP_HEADER_BYTES:
        return None
    if packet[0] >> 6 != RTP_VERSION or packet[1] & 0x7F != DISCORD_VOICE_PAYLOAD_TYPE:
        return None
    source_end = RTP_SYNCHRONIZATION_SOURCE_OFFSET + 4
    return int.from_bytes(packet[RTP_SYNCHRONIZATION_SOURCE_OFFSET:source_end], "big")


class SustainedSpeechDetector:
    def __init__(self, maximum_gap_seconds):
        self._maximum_gap_seconds = maximum_gap_seconds
        self._voiced_seconds = 0.0
        self._last_voiced_at = float("-inf")

    def observe_voiced_frame(self, observed_at, frame_seconds):
        if observed_at - self._last_voiced_at > self._maximum_gap_seconds:
            self._voiced_seconds = 0.0
        self._voiced_seconds += frame_seconds
        self._last_voiced_at = observed_at

    def sustained_seconds(self, now):
        if now - self._last_voiced_at > self._maximum_gap_seconds:
            return 0.0
        return self._voiced_seconds

    def reset(self):
        self._voiced_seconds = 0.0
        self._last_voiced_at = float("-inf")


class ListenerKeyAttempt:
    def __init__(self, dave_session, listener_user_id):
        self._dave_session = dave_session
        self._listener_user_id = listener_user_id
        self.opened = False

    def decrypt(self, _user_id, media_type, frame):
        if not frame.endswith(DAVE_FRAME_MARKER):
            raise ValueError("frame_carries_no_sender_key")
        try:
            decrypted = self._dave_session.decrypt(
                self._listener_user_id, media_type, frame
            )
        except Exception as error:
            raise ValueError("frame_not_from_listener") from error
        self.opened = True
        return decrypted
