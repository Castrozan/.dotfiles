from voice_bridge.listener_stream import (
    rtp_synchronization_source,
    source_belongs_to_listener,
)

LISTENER = 100
STRANGER = 200


def test_reads_the_source_from_the_rtp_header():
    packet = bytes(8) + (0x01020304).to_bytes(4, "big") + b"payload"

    assert rtp_synchronization_source(packet) == 0x01020304


def test_a_truncated_packet_has_no_source():
    assert rtp_synchronization_source(bytes(11)) is None


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
