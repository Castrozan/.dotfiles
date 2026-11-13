import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import local_seat
import mac_wake_boundaries
import pytest
import wake_boundaries
import wake_listener
from conversation_addressee import Addressee
from transcription import transcriber
from wake_phrase import LiveSession

VOYAGER = LiveSession("Voyager", "wW:pPZ")


@pytest.fixture
def on_a_mac(monkeypatch):
    monkeypatch.setattr(wake_boundaries.sys, "platform", "darwin")
    monkeypatch.setenv(mac_wake_boundaries.HOST_ENVIRONMENT_VARIABLE, "kira")
    return wake_boundaries.for_this_machine()


def ran(monkeypatch, stdout=b"", returncode=0):
    runner = Mock(return_value=SimpleNamespace(stdout=stdout, returncode=returncode))
    monkeypatch.setattr(mac_wake_boundaries.subprocess, "run", runner)
    return runner


def test_a_mac_captures_through_the_microphone_page_relay(on_a_mac):
    command = on_a_mac.capture_command()
    assert command[0] == sys.executable
    assert command[1].endswith("scripts/wake/mac_microphone.py")


def test_other_systems_keep_the_pulseaudio_capture_and_local_effects(monkeypatch):
    monkeypatch.setattr(wake_boundaries.sys, "platform", "linux")
    boundaries = wake_boundaries.for_this_machine()
    assert boundaries.capture_command()[0] == "parec"
    assert boundaries.transcribe is transcriber.transcribe
    assert boundaries.open_conversation is wake_boundaries.conversation_opened


def test_transcription_streams_the_pcm_to_the_avatar_host(monkeypatch, on_a_mac):
    runner = ran(monkeypatch, stdout="  hey Voyager, check the build \n".encode())
    assert on_a_mac.transcribe(b"pcm") == "hey Voyager, check the build"
    assert runner.call_args.args[0] == [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=5",
        "chise",
        "avatar-transcribe",
    ]
    assert runner.call_args.kwargs["input"] == b"pcm"
    assert runner.call_args.kwargs["timeout"] > 0


def test_a_failed_transcription_is_a_subprocess_error_the_wake_drops(
    monkeypatch, on_a_mac
):
    monkeypatch.setattr(
        mac_wake_boundaries.subprocess,
        "run",
        Mock(side_effect=subprocess.CalledProcessError(255, "ssh")),
    )
    reported = Mock()
    on_a_mac.report = reported
    wake_listener.WakeListener(on_a_mac, dry_run=False).hear(b"pcm")
    assert "Dropped an utterance" in reported.call_args.args[0]


def test_opening_seats_the_conversation_at_this_mac_whatever_the_idle_time(
    monkeypatch, on_a_mac
):
    runner = ran(monkeypatch)
    assert on_a_mac.open_conversation() is True
    assert runner.call_args.args[0] == ["avatar-talk", "open", "--seat", "remote"]
    assert runner.call_args.kwargs["timeout"] > 0
    ran(monkeypatch, returncode=1)
    assert on_a_mac.open_conversation() is False


def test_the_floor_goes_to_the_woken_pane_on_this_host_through_the_avatar_host(
    monkeypatch, on_a_mac
):
    runner = ran(monkeypatch)
    on_a_mac.hand_to(Addressee(VOYAGER.pane, VOYAGER.servant, 0))
    assert runner.call_args.args[0][-2:] == [
        "chise",
        "avatar-claim-floor --agent kira:wW:pPZ",
    ]
    assert runner.call_args.kwargs["check"] is True


def test_a_conversation_has_no_transcript_purpose_or_addressee_on_a_mac(on_a_mac):
    assert on_a_mac.transcript_entries() == []
    assert on_a_mac.listening_purpose() is None
    assert on_a_mac.addressee() is None


@pytest.mark.parametrize(
    ("seat", "armed"),
    [
        (None, True),
        ({"attached": True, "listening": False, "meeting": True}, True),
        ({"attached": True, "listening": True, "meeting": True}, False),
        ({"attached": True, "listening": True}, False),
    ],
)
def test_only_a_conversation_listening_at_this_seat_pauses_the_wake(
    monkeypatch, seat, armed
):
    monkeypatch.setattr(wake_boundaries.sys, "platform", "darwin")
    monkeypatch.setattr(local_seat, "health", lambda: seat)
    boundaries = wake_boundaries.for_this_machine()
    boundaries.sessions = Mock(return_value=[VOYAGER])
    assert wake_listener.WakeListener(boundaries, False).armed() is armed
