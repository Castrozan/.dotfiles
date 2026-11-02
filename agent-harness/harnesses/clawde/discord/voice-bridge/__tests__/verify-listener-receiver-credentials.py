import struct
from types import SimpleNamespace

from voice_bridge.listener_receiver import ListenerVoiceReceiver

LISTENER_USER_ID = 42
LISTENER_SOURCE = 2
SECRET_KEY = bytes(32)


def receiver_connected_with(dave_session):
    connection = SimpleNamespace(
        secret_key=list(SECRET_KEY), dave_session=dave_session, ssrc=1
    )
    receiver = ListenerVoiceReceiver(
        SimpleNamespace(_connection=connection), LISTENER_USER_ID
    )
    receiver._running = True
    return receiver


def rtp_packet():
    return struct.pack(">BBHII", 0x80, 0x78, 1, 1, LISTENER_SOURCE) + bytes(24)


def test_reads_the_live_transport_key_for_each_packet():
    receiver = receiver_connected_with(None)
    receiver._on_packet(rtp_packet())
    assert receiver._secret_key == SECRET_KEY


def test_forgets_a_source_whose_frame_the_listener_key_cannot_open():
    receiver = receiver_connected_with(object())
    receiver._on_packet(rtp_packet())
    assert LISTENER_SOURCE not in receiver._ssrc_to_user
    assert receiver.listener_packet_count == 0


def test_routes_a_known_listener_source_through_the_live_session():
    dave_session = object()
    receiver = receiver_connected_with(dave_session)
    receiver.map_ssrc(LISTENER_SOURCE, LISTENER_USER_ID)
    receiver._on_packet(rtp_packet())
    assert receiver._dave_session is dave_session
    assert receiver.listener_packet_count == 1


test_reads_the_live_transport_key_for_each_packet()
test_forgets_a_source_whose_frame_the_listener_key_cannot_open()
test_routes_a_known_listener_source_through_the_live_session()
