from voice_bridge.listener_stream import (
    rtp_synchronization_source,
    source_belongs_to_listener,
)

LISTENER = 100
STRANGER = 200


def voice_packet(source):
    return b"\x80\x78" + bytes(6) + source.to_bytes(4, "big") + b"payload"


def test_reads_the_source_from_the_rtp_header():
    packet = voice_packet(0x01020304)

    assert rtp_synchronization_source(packet) == 0x01020304


def test_a_truncated_packet_has_no_source():
    assert rtp_synchronization_source(voice_packet(1)[:11]) is None


def test_a_control_packet_has_no_voice_source():
    assert rtp_synchronization_source(b"\x80\xc8" + voice_packet(1)[2:]) is None


def test_a_mapped_listener_source_is_admitted():
    assert source_belongs_to_listener(1, LISTENER, {1: LISTENER}, {LISTENER, STRANGER})


def test_a_mapped_stranger_source_is_refused_even_when_alone():
    assert not source_belongs_to_listener(1, LISTENER, {1: STRANGER}, {LISTENER})


def test_an_unmapped_source_is_refused_when_the_listener_has_another_one():
    assert not source_belongs_to_listener(2, LISTENER, {1: LISTENER}, {LISTENER})


def test_an_unmapped_source_is_refused_when_a_stranger_shares_the_channel():
    assert not source_belongs_to_listener(1, LISTENER, {}, {LISTENER, STRANGER})


def test_an_unmapped_source_is_the_listener_when_they_are_alone_in_the_channel():
    assert source_belongs_to_listener(1, LISTENER, {}, {LISTENER})
