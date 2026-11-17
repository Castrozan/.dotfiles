import json

import conversation_addressee
import listener_runtime
import mac_wake_boundaries
import pytest
import transcript_log
import wake_boundaries
from avatar_host_runner import ran
from conversation_addressee import Addressee

HOLDER = Addressee("w1:p1", "Sasaki Kojirou", 3)


@pytest.fixture
def a_mac_with_records(monkeypatch, tmp_path, seat_listening):
    seat_listening.listening = False
    monkeypatch.setattr(listener_runtime, "runtime_directory", lambda: tmp_path)
    monkeypatch.setattr(wake_boundaries.sys, "platform", "darwin")
    monkeypatch.setenv(mac_wake_boundaries.HOST_ENVIRONMENT_VARIABLE, "kira")
    return wake_boundaries.for_this_machine()


def test_a_conversation_on_this_mac_counts_as_listening(
    a_mac_with_records, conversation_here
):
    assert a_mac_with_records.conversation_listening() is False
    conversation_here.listening = True
    assert a_mac_with_records.conversation_listening() is True


def test_a_conversation_on_this_mac_is_read_and_handed_over_without_the_host(
    monkeypatch, a_mac_with_records, conversation_here, tmp_path
):
    conversation_here.listening = True
    runner = ran(monkeypatch, "")
    transcript_log.append(tmp_path / "transcript.jsonl", "human", "Hey Sasaki", None)
    a_mac_with_records.hand_to(HOLDER)
    assert [entry["text"] for entry in a_mac_with_records.transcript_entries()] == [
        "Hey Sasaki"
    ]
    assert a_mac_with_records.addressee() == HOLDER
    assert conversation_addressee.current(tmp_path) == HOLDER
    assert not runner.called


def test_with_no_conversation_here_the_room_is_handed_over_at_the_host(
    monkeypatch, a_mac_with_records
):
    runner = ran(monkeypatch, json.dumps(None))
    a_mac_with_records.hand_to(HOLDER)
    assert "avatar-claim-floor" in runner.call_args.args[0][-1]
