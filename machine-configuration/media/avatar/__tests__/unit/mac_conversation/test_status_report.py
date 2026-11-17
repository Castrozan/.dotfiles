import json

import conversation_effects
import conversation_report
import conversation_seat
import conversation_state
import mac_talk
import pytest
import utterances
from conversation_state import ConversationPhase

STATUS_KEYS = ["open", "live", "seat", "last_heard"]


@pytest.fixture(autouse=True)
def nothing_heard_yet(monkeypatch):
    monkeypatch.setattr(utterances, "last_heard", lambda directory: 0)


def printed_status(function, directory, capsys):
    function(None, directory)
    return json.loads(capsys.readouterr().out)


def test_the_status_report_has_the_keys_agents_parse_in_order(tmp_path, capsys):
    conversation_report.print_status(tmp_path, is_open=True, live=False, seat="room")
    assert json.loads(capsys.readouterr().out) == {
        "open": True,
        "live": False,
        "seat": "room",
        "last_heard": 0,
    }
    conversation_report.print_status(tmp_path, is_open=False, live=False, seat=None)
    assert list(json.loads(capsys.readouterr().out)) == STATUS_KEYS


def test_the_closed_report_says_only_that_nothing_is_open(capsys):
    conversation_report.print_closed()
    assert json.loads(capsys.readouterr().out) == {"open": False}


@pytest.mark.parametrize("phase", [ConversationPhase.OPEN, ConversationPhase.CLOSED])
def test_the_host_and_the_mac_print_the_same_status_shape(
    monkeypatch, tmp_path, capsys, phase
):
    monkeypatch.setattr(conversation_state, "observe", lambda directory: phase)
    monkeypatch.setattr(conversation_seat, "configured", lambda directory: "room")
    host = printed_status(conversation_effects.status, tmp_path, capsys)
    mac = printed_status(mac_talk.status, tmp_path, capsys)
    assert list(host) == list(mac) == STATUS_KEYS
    assert host == mac
