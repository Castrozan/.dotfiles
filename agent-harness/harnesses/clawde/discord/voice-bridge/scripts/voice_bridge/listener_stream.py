RTP_HEADER_BYTES = 12
RTP_SYNCHRONIZATION_SOURCE_OFFSET = 8
RTP_VERSION = 2
DISCORD_VOICE_PAYLOAD_TYPE = 0x78


def rtp_synchronization_source(packet):
    if len(packet) < RTP_HEADER_BYTES:
        return None
    if packet[0] >> 6 != RTP_VERSION or packet[1] & 0x7F != DISCORD_VOICE_PAYLOAD_TYPE:
        return None
    source_end = RTP_SYNCHRONIZATION_SOURCE_OFFSET + 4
    return int.from_bytes(packet[RTP_SYNCHRONIZATION_SOURCE_OFFSET:source_end], "big")


def source_belongs_to_listener(
    source, listener_user_id, user_by_source, channel_occupants
):
    known_user = user_by_source.get(source)
    if known_user is not None:
        return known_user == listener_user_id
    if listener_user_id in user_by_source.values():
        return False
    return channel_occupants == {listener_user_id}
