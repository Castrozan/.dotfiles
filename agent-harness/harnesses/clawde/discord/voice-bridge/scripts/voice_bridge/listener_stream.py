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
