import sys

from room_audio import DEFAULT_SINK, LIP_SYNC_SINK

__all__ = ["DEFAULT_SINK", "LIP_SYNC_SINK", "Speaker", "microphone_chunks"]


def boundaries_of(platform):
    if platform == "darwin":
        import mac_room_audio

        return mac_room_audio.Speaker, mac_room_audio.microphone_chunks
    import room_audio

    return room_audio.Speaker, room_audio.microphone_chunks


Speaker, microphone_chunks = boundaries_of(sys.platform)
