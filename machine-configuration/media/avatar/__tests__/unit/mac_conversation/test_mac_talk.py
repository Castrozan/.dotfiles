import contextlib
import json
from types import SimpleNamespace
from unittest.mock import Mock

import conversation_addressee
import mac_talk
import pytest
from conversation_addressee import Addressee
from conversation_state import ConversationPhase

SPEECH = SimpleNamespace(text="Good evening", emotion="neutral", voice=None)
OPENING = SimpleNamespace(language="en", character="swordsman")
LISTENING_AT_THE_HOST = {"attached": True, "listening": True}
IDLE_AT_THE_HOST = {"attached": True, "listening": False}


@pytest.fixture(autouse=True)
def this_mac(monkeypatch, tmp_path):
    mac = SimpleNamespace(
        tunnel=None,
        attached=True,
        phase=ConversationPhase.OPEN,
        begin=Mock(),
        stop=Mock(),
        close_browser=Mock(),
        host=Mock(return_value=7),
        leave=Mock(),
        stage=Mock(),
    )
    mac.stage.standing = contextlib.nullcontext
    monkeypatch.delenv("HERDR_PANE_ID", raising=False)
    monkeypatch.setattr(
        mac_talk.listener_runtime, "runtime_directory", lambda: tmp_path / "runtime"
    )
    monkeypatch.setattr(mac_talk, "mac_stage", mac.stage)
    monkeypatch.setattr(mac_talk.local_seat, "health", lambda: mac.tunnel)
    monkeypatch.setattr(mac_talk.local_seat, "leave", mac.leave)
    monkeypatch.setattr(mac_talk.mac_seat_client, "attached", lambda: mac.attached)
    monkeypatch.setattr(mac_talk.mac_seat_client, "hush", Mock())
    monkeypatch.setattr(mac_talk.mac_seat_client, "close_browser", mac.close_browser)
    monkeypatch.setattr(mac_talk.listener_session, "begin_listening", mac.begin)
    monkeypatch.setattr(mac_talk.listener_session, "stop_listening", mac.stop)
    monkeypatch.setattr(mac_talk.conversation_state, "observe", lambda _: mac.phase)
    monkeypatch.setattr(mac_talk.remote_talk, "carry_out", mac.host)
    monkeypatch.setattr(
        mac_talk.remote_talk,
        "with_the_agent_that_receives_live_tasks",
        lambda arguments: arguments,
    )
    return mac


def test_what_only_the_avatar_host_offers_goes_to_the_host(this_mac):
    arguments = ["open", "--seat", "room"]
    this_mac.phase = ConversationPhase.CLOSED
    assert mac_talk.carry_out(arguments) == 7
    this_mac.host.assert_called_once_with(arguments)
    assert not this_mac.stop.called


def test_opening_at_the_host_first_ends_the_conversation_held_here(this_mac):
    assert mac_talk.carry_out(["open", "--seat", "remote"]) == 7
    this_mac.stop.assert_called_once_with()
    this_mac.stage.strike.assert_called_once_with()


@pytest.mark.parametrize("arguments", [["say", "hello"], ["status"], ["show"]])
def test_a_conversation_listening_at_the_host_keeps_its_verbs_there(
    this_mac, arguments
):
    this_mac.tunnel = LISTENING_AT_THE_HOST
    assert mac_talk.carry_out(arguments) == 7


def test_a_seat_the_host_stopped_using_does_not_draw_speech_to_the_host(this_mac):
    this_mac.tunnel = IDLE_AT_THE_HOST
    assert mac_talk.carry_out(["say", "Good evening", "happy"]) == 0
    assert not this_mac.host.called
    this_mac.stage.speak.assert_called_once_with("Good evening", "happy", None)


def test_the_window_is_shown_and_hidden_on_this_mac(this_mac):
    assert mac_talk.carry_out(["show"]) == 0
    assert mac_talk.carry_out(["hide"]) == 0
    this_mac.stage.show_window.assert_called_once_with()
    this_mac.stage.hide_window.assert_called_once_with()


def test_a_session_the_room_did_not_turn_to_may_not_speak(
    this_mac, tmp_path, monkeypatch
):
    conversation_addressee.hand_to(tmp_path, Addressee("w1:p1", "Sasaki Kojirou", 0))
    monkeypatch.setenv("HERDR_PANE_ID", "w9:p9")
    with pytest.raises(RuntimeError, match="holds the room"):
        mac_talk.speak(SPEECH, tmp_path)
    assert not this_mac.stage.speak.called


def test_speaking_marks_the_conversation_as_not_quiet(this_mac, tmp_path):
    mac_talk.speak(SPEECH, tmp_path)
    assert (tmp_path / mac_talk.listener_session.SPOKEN_FILE).exists()


def test_opening_sets_the_stage_shows_the_character_and_listens(
    this_mac, tmp_path, capsys
):
    mac_talk.open_conversation(OPENING, tmp_path)
    this_mac.stage.set_up.assert_called_once_with()
    this_mac.stage.show_character.assert_called_once_with("swordsman")
    assert this_mac.begin.call_args.kwargs == {"language": "en", "barge_in": True}
    assert json.loads(capsys.readouterr().out)["open"] is True


def test_opening_here_leaves_a_seat_the_host_stopped_using(this_mac, tmp_path):
    this_mac.tunnel = IDLE_AT_THE_HOST
    mac_talk.open_conversation(OPENING, tmp_path)
    this_mac.leave.assert_called_once_with()


def test_a_seat_kept_for_a_meeting_is_left_alone(this_mac, tmp_path):
    this_mac.tunnel = IDLE_AT_THE_HOST | {"meeting": True}
    mac_talk.open_conversation(OPENING, tmp_path)
    assert not this_mac.leave.called


def test_an_opening_whose_page_never_attaches_leaves_nothing_running(
    this_mac, tmp_path, monkeypatch
):
    this_mac.attached = False
    monkeypatch.setattr(mac_talk, "ATTACH_WAIT_SECONDS", -1)
    with pytest.raises(TimeoutError, match="did not attach"):
        mac_talk.open_conversation(OPENING, tmp_path)
    this_mac.stop.assert_called_once_with()
    this_mac.close_browser.assert_called_once_with()
    this_mac.stage.strike.assert_called_once_with()


def test_closing_leaves_no_record_of_what_was_said(this_mac, tmp_path, capsys):
    for record in mac_talk.listener_session.SESSION_RECORDS:
        (tmp_path / record).write_text("private")
    conversation_addressee.hand_to(tmp_path, Addressee("w1:p1", "Sasaki Kojirou", 0))
    mac_talk.close_conversation(SimpleNamespace(), tmp_path)
    assert [path.name for path in tmp_path.iterdir() if path.is_file()] == [
        conversation_addressee.LOCK_FILE
    ]
    assert json.loads(capsys.readouterr().out) == {"open": False}


def test_hearing_a_closed_conversation_is_refused(this_mac):
    this_mac.phase = ConversationPhase.CLOSED
    with pytest.raises(mac_talk.utterances.ConversationClosed):
        mac_talk.carry_out(["hear"])
