import json
import subprocess
from unittest.mock import Mock

import mac_wake_boundaries
import pytest
from avatar_host_runner import ran, remote_command
from listener_session import ListenerPurpose
from wake_phrase import LiveSession

VOYAGER = LiveSession("Voyager", "wW:pPZ")
ENTRIES = [
    {
        "sequence": 1,
        "time": 1.5,
        "source": "human",
        "text": "Olá Voyager, status",
        "speaker": "Lucas",
        "turn_finished": True,
    },
    {
        "sequence": 2,
        "time": 2.5,
        "source": "meeting",
        "text": "outra coisa",
        "speaker": None,
        "turn_finished": False,
    },
]


def lines_of(entries):
    return "".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in entries)


def test_entries_come_back_in_the_shape_the_avatar_host_logs_them(
    monkeypatch, on_a_mac
):
    runner = ran(monkeypatch, lines_of(ENTRIES))
    assert on_a_mac.transcript_entries() == ENTRIES
    assert runner.call_args.args[0] == [
        *mac_wake_boundaries.REACH_AVATAR_HOST,
        "avatar-listen read --since 0",
    ]
    assert runner.call_args.kwargs["timeout"] > 0
    assert runner.call_args.kwargs["check"] is True


def test_an_empty_transcript_is_no_entries(monkeypatch, on_a_mac):
    ran(monkeypatch, "")
    assert on_a_mac.transcript_entries() == []


def test_ticks_inside_the_reuse_window_share_one_remote_read(
    monkeypatch, on_a_mac, clock
):
    runner = ran(monkeypatch, lines_of(ENTRIES))
    for _ in range(5):
        assert on_a_mac.transcript_entries() == ENTRIES
        clock.now += 0.2
    assert runner.call_count == 1
    clock.now += mac_wake_boundaries.CONVERSATION_READ_REUSE_SECONDS
    on_a_mac.transcript_entries()
    assert runner.call_count == 2


def test_a_failed_read_is_not_retried_inside_the_reuse_window(
    monkeypatch, on_a_mac, clock
):
    runner = Mock(side_effect=subprocess.CalledProcessError(255, "ssh"))
    monkeypatch.setattr(mac_wake_boundaries.subprocess, "run", runner)
    with pytest.raises(subprocess.CalledProcessError):
        on_a_mac.transcript_entries()
    clock.now += 0.2
    assert on_a_mac.transcript_entries() == []
    assert runner.call_count == 1


def test_nothing_is_asked_of_the_avatar_host_while_the_seat_is_not_listening(
    monkeypatch, on_a_mac, seat_listening
):
    runner = ran(monkeypatch, lines_of(ENTRIES))
    seat_listening.listening = False
    assert on_a_mac.transcript_entries() == []
    assert on_a_mac.listening_purpose() is None
    assert on_a_mac.addressee() is None
    runner.assert_not_called()


def test_a_new_conversation_does_not_reuse_the_previous_one(
    monkeypatch, on_a_mac, seat_listening, clock
):
    runner = ran(monkeypatch, lines_of(ENTRIES))
    on_a_mac.transcript_entries()
    seat_listening.listening = False
    on_a_mac.transcript_entries()
    seat_listening.listening = True
    on_a_mac.transcript_entries()
    assert runner.call_count == 2


@pytest.mark.parametrize(
    ("status", "purpose"),
    [
        ({"listening": True, "purpose": "conversation"}, ListenerPurpose.CONVERSATION),
        ({"listening": True, "purpose": "meeting"}, ListenerPurpose.MEETING),
        ({"listening": False, "purpose": "meeting"}, None),
        ({"listening": True, "purpose": None}, None),
        ({"listening": True, "purpose": "unknown"}, None),
    ],
)
def test_the_live_purpose_is_the_configured_one_only_while_the_avatar_host_listens(
    monkeypatch, on_a_mac, status, purpose
):
    runner = ran(monkeypatch, json.dumps(status))
    assert on_a_mac.listening_purpose() == purpose
    assert remote_command(runner) == "avatar-listen status"
