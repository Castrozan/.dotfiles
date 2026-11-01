import pytest

from voice_bridge.listener_stream import (
    DAVE_FRAME_MARKER,
    ListenerKeyAttempt,
    SustainedSpeechDetector,
    rtp_synchronization_source,
)

LISTENER = 100
AUDIO = "audio"
PROTECTED_FRAME = b"ciphertext" + DAVE_FRAME_MARKER


def voice_packet(source):
    return b"\x80\x78" + bytes(6) + source.to_bytes(4, "big") + b"payload"


class FakeDaveSession:
    def __init__(self, opens_for=None):
        self._opens_for = opens_for
        self.attempted_users = []

    def decrypt(self, user_id, _media_type, frame):
        self.attempted_users.append(user_id)
        if user_id != self._opens_for:
            raise RuntimeError("Unencrypted passthrough refused")
        return frame.removesuffix(DAVE_FRAME_MARKER)


def test_reads_the_source_from_the_rtp_header():
    assert rtp_synchronization_source(voice_packet(0x01020304)) == 0x01020304


def test_a_truncated_packet_has_no_source():
    assert rtp_synchronization_source(voice_packet(1)[:11]) is None


def test_a_control_packet_has_no_voice_source():
    assert rtp_synchronization_source(b"\x80\xc8" + voice_packet(1)[2:]) is None


def test_a_frame_the_listener_key_opens_attributes_the_source():
    attempt = ListenerKeyAttempt(FakeDaveSession(opens_for=LISTENER), LISTENER)

    assert attempt.decrypt(0, AUDIO, PROTECTED_FRAME) == b"ciphertext"
    assert attempt.opened


def test_the_attempt_always_tries_the_listener_key():
    session = FakeDaveSession(opens_for=LISTENER)

    ListenerKeyAttempt(session, LISTENER).decrypt(999, AUDIO, PROTECTED_FRAME)

    assert session.attempted_users == [LISTENER]


def test_a_stranger_frame_stays_closed_without_passing_as_unencrypted():
    attempt = ListenerKeyAttempt(FakeDaveSession(opens_for=200), LISTENER)

    with pytest.raises(ValueError) as refusal:
        attempt.decrypt(0, AUDIO, PROTECTED_FRAME)

    assert "Unencrypted" not in str(refusal.value)
    assert not attempt.opened


def test_an_unprotected_silence_frame_attributes_nothing():
    attempt = ListenerKeyAttempt(FakeDaveSession(opens_for=LISTENER), LISTENER)

    with pytest.raises(ValueError):
        attempt.decrypt(0, AUDIO, b"\xf8\xff\xfe")

    assert not attempt.opened


def detector_after_frames(detector, observed_times):
    for observed_at in observed_times:
        detector.observe_voiced_frame(observed_at, 0.02)
    return detector


def test_continuous_voiced_frames_accumulate():
    detector = detector_after_frames(
        SustainedSpeechDetector(0.2), [index * 0.02 for index in range(30)]
    )

    assert round(detector.sustained_seconds(0.58), 2) == 0.6


def test_blips_separated_by_silence_never_accumulate():
    detector = detector_after_frames(
        SustainedSpeechDetector(0.2), [0.0, 0.02, 0.5, 0.52, 1.0, 1.02]
    )

    assert round(detector.sustained_seconds(1.02), 2) == 0.04


def test_speech_expires_after_the_gap():
    detector = detector_after_frames(SustainedSpeechDetector(0.2), [0.0, 0.02])

    assert detector.sustained_seconds(0.5) == 0.0


def test_forgetting_clears_accumulated_speech():
    detector = detector_after_frames(SustainedSpeechDetector(0.2), [0.0, 0.02])

    detector.reset()

    assert detector.sustained_seconds(0.03) == 0.0
