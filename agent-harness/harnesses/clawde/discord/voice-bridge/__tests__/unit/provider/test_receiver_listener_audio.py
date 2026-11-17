import struct
import threading
from collections import defaultdict
from types import ModuleType, SimpleNamespace

import pytest

from provider_fixtures import load_module
from voice_provider.listener_audio_tap import (
    CAPTURE_FRAME_BYTES,
    SILENCE_FRAME,
    ListenerAudioTap,
)

LISTENER_USER_ID = 42
LISTENER_SOURCE = 7
STRANGER_USER_ID = 43
STRANGER_SOURCE = 8
DECODED_FRAME = struct.pack("<hh", 900, 900) * 960


class FakeOpusDecoder:
    def decode(self, payload):
        return payload


class FakeVoiceReceiver:
    def __init__(self, voice_client, allowed_user_ids=None):
        self._vc = voice_client
        self._lock = threading.Lock()
        self._buffers = defaultdict(bytearray)
        self._decoders = {}
        self._last_packet_time = {}
        self._ssrc_to_user = {}
        self._bot_ssrc = 0
        self._creds = (b"", None, 0, False)

    @property
    def _dave_session(self):
        return self._creds[1]

    def _resolve_credentials(self, _connection):
        return None

    def map_ssrc(self, source, user_id):
        with self._lock:
            self._ssrc_to_user[source] = user_id

    def _on_packet(self, data):
        source = int.from_bytes(data[8:12], "big")
        payload = data[12:]
        if not payload:
            return
        if source not in self._decoders:
            self._decoders[source] = FakeOpusDecoder()
        decoded = self._decoders[source].decode(payload)
        with self._lock:
            self._buffers[source].extend(decoded)
            self._last_packet_time[source] = 0.0


def fake_modules():
    adapter = ModuleType("plugins.platforms.discord.adapter")
    adapter.VoiceReceiver = FakeVoiceReceiver
    discord = ModuleType("discord")
    discord.opus = SimpleNamespace(Decoder=FakeOpusDecoder)
    return {
        "discord": discord,
        "plugins": ModuleType("plugins"),
        "plugins.platforms": ModuleType("plugins.platforms"),
        "plugins.platforms.discord": ModuleType("plugins.platforms.discord"),
        "plugins.platforms.discord.adapter": adapter,
    }


@pytest.fixture
def receiver_and_tap():
    module = load_module(
        "listener_receiver_under_test",
        "voice_bridge/listener_receiver.py",
        fake_modules(),
    )
    tap = ListenerAudioTap()
    receiver = module.ListenerVoiceReceiver(
        SimpleNamespace(_connection=None), LISTENER_USER_ID, tap
    )
    receiver.map_ssrc(LISTENER_SOURCE, LISTENER_USER_ID)
    receiver.map_ssrc(STRANGER_SOURCE, STRANGER_USER_ID)
    return receiver, tap


def voice_packet(source, payload):
    return b"\x80\x78" + bytes(6) + source.to_bytes(4, "big") + payload


def test_the_listener_audio_reaches_the_tap_and_is_not_kept_in_the_receiver(
    receiver_and_tap,
):
    receiver, tap = receiver_and_tap
    receiver._on_packet(voice_packet(LISTENER_SOURCE, DECODED_FRAME))
    expected = struct.pack("<h", 900) * (CAPTURE_FRAME_BYTES // 2)
    assert tap.take_frame() == expected
    assert tap.take_frame() == SILENCE_FRAME
    assert not receiver._buffers
    assert not receiver._last_packet_time
    assert receiver.listener_packet_count == 1


def test_another_speaker_never_reaches_the_tap(receiver_and_tap):
    receiver, tap = receiver_and_tap
    receiver._on_packet(voice_packet(STRANGER_SOURCE, DECODED_FRAME))
    assert tap.take_frame() == SILENCE_FRAME
    assert receiver.listener_packet_count == 0


def test_a_packet_that_decodes_to_nothing_does_not_repeat_the_last_frame(
    receiver_and_tap,
):
    receiver, tap = receiver_and_tap
    receiver._on_packet(voice_packet(LISTENER_SOURCE, DECODED_FRAME))
    receiver._on_packet(voice_packet(LISTENER_SOURCE, b""))
    assert tap.take_frame() != SILENCE_FRAME
    assert tap.take_frame() == SILENCE_FRAME
