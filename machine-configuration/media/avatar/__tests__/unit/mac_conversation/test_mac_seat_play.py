import wave
from unittest.mock import Mock

import mac_seat_play
import pytest

SAMPLES = b"\x01\x02" * 240


@pytest.fixture
def recording(tmp_path):
    path = tmp_path / "speech.wav"
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(24000)
        audio.writeframes(SAMPLES)
    return str(path)


def test_with_a_seat_the_samples_play_through_its_page(monkeypatch, recording):
    played = Mock()
    monkeypatch.setattr(mac_seat_play.mac_seat_client, "attached", lambda: True)
    monkeypatch.setattr(mac_seat_play.mac_seat_client, "play", played)
    mac_seat_play.play(recording)
    played.assert_called_once_with(SAMPLES)


def test_without_a_seat_the_recording_plays_through_the_speakers(
    monkeypatch, recording
):
    ran = Mock()
    monkeypatch.setattr(mac_seat_play.mac_seat_client, "attached", lambda: False)
    monkeypatch.setattr(mac_seat_play.subprocess, "run", ran)
    mac_seat_play.play(recording)
    assert ran.call_args.args[0] == [mac_seat_play.PLAYER, recording]
    assert ran.call_args.kwargs["timeout"] == mac_seat_play.PLAYBACK_TIMEOUT_SECONDS


def test_being_stopped_hushes_the_seat_before_leaving(monkeypatch):
    hush = Mock()
    monkeypatch.setattr(mac_seat_play.mac_seat_client, "hush", hush)
    with pytest.raises(SystemExit):
        mac_seat_play.hush_and_leave(15, None)
    hush.assert_called_once_with()
