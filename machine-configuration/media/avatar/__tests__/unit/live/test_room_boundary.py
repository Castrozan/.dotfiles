import mac_room_audio
import room_audio
import room_boundary
import pytest


@pytest.mark.parametrize("platform", ["linux", "freebsd"])
def test_every_platform_but_a_mac_plays_and_listens_through_the_sound_server(platform):
    assert room_boundary.boundaries_of(platform) == (
        room_audio.Speaker,
        room_audio.microphone_chunks,
    )


def test_a_mac_plays_and_listens_through_the_seat_page():
    assert room_boundary.boundaries_of("darwin") == (
        mac_room_audio.Speaker,
        mac_room_audio.microphone_chunks,
    )


def test_both_boundaries_answer_to_the_same_speaker_interface():
    for speaker in (room_audio.Speaker, mac_room_audio.Speaker):
        for method in ("play", "buffered_seconds", "clear", "close"):
            assert callable(getattr(speaker, method))


def test_the_bridge_keeps_the_sinks_the_room_seats_name():
    assert room_boundary.DEFAULT_SINK is room_audio.DEFAULT_SINK
    assert room_boundary.LIP_SYNC_SINK == room_audio.LIP_SYNC_SINK
