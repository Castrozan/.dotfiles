import sys

import pytest

import listener
import mac_seat_client
import source_capture

DISCORD_COMMAND = ["discord-voice", "capture"]


@pytest.mark.parametrize("platform", ["linux", "darwin"])
def test_the_discord_device_captures_from_the_discord_bridge_on_any_platform(
    monkeypatch, platform
):
    monkeypatch.setattr(sys, "platform", platform)
    capture_command, _ = listener.boundaries_of_this_machine()
    assert capture_command(source_capture.DISCORD_DEVICE) == DISCORD_COMMAND


def test_other_devices_keep_the_pulse_capture_on_linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    capture_command, stop_speaking = listener.boundaries_of_this_machine()
    assert capture_command("headset") == source_capture.capture_command("headset")
    assert stop_speaking is listener.interrupt_speaker


def test_other_devices_keep_the_mac_seat_capture_on_darwin(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    capture_command, stop_speaking = listener.boundaries_of_this_machine()
    assert capture_command("headset") == mac_seat_client.capture_command("headset")
    assert stop_speaking is mac_seat_client.hush


def test_every_capture_of_the_discord_device_gets_its_own_command_list():
    capture_command = source_capture.capture_command_by_device(lambda device: [])
    capture_command(source_capture.DISCORD_DEVICE).append("changed")
    assert capture_command(source_capture.DISCORD_DEVICE) == DISCORD_COMMAND
