import json
from types import SimpleNamespace
from unittest.mock import Mock

import conversation_addressee
import mac_talk
import pytest
from conversation_addressee import Addressee
from conversation_state import ConversationPhase

SPEECH = SimpleNamespace(text="Good evening", emotion="neutral", voice=None)
OPENING = SimpleNamespace(language="en", character=None)


@pytest.fixture(autouse=True)
def this_mac(monkeypatch, tmp_path):
    mac = SimpleNamespace(
        tunnel=None,
        attached=True,
        phase=ConversationPhase.OPEN,
        played=[],
        played_without_a_seat=[],
        synthesized=[],
        begin=Mock(),
        stop=Mock(),
        close_browser=Mock(),
        hush=Mock(),
        host=Mock(return_value=7),
        leave=Mock(),
    )
    monkeypatch.delenv("HERDR_PANE_ID", raising=False)
    monkeypatch.setattr(
        mac_talk.listener_runtime, "runtime_directory", lambda: tmp_path / "runtime"
    )
    monkeypatch.setattr(mac_talk.local_seat, "health", lambda: mac.tunnel)
    monkeypatch.setattr(mac_talk.local_seat, "leave", mac.leave)
    monkeypatch.setattr(mac_talk.mac_seat_client, "attached", lambda: mac.attached)
    monkeypatch.setattr(mac_talk.mac_seat_client, "play", mac.played.append)
    monkeypatch.setattr(mac_talk.mac_seat_client, "hush", mac.hush)
    monkeypatch.setattr(mac_talk.mac_seat_client, "close_browser", mac.close_browser)
    monkeypatch.setattr(mac_talk.mac_speech, "voice_of", lambda servant: f"{servant}")
    monkeypatch.setattr(
        mac_talk.mac_speech,
        "synthesized",
        lambda *asked: mac.synthesized.append(asked) or "speech.wav",
    )
    monkeypatch.setattr(mac_talk.mac_speech, "samples_of", lambda recording: b"pcm")
    monkeypatch.setattr(
        mac_talk.mac_speech, "play_without_a_seat", mac.played_without_a_seat.append
    )
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


@pytest.mark.parametrize(
    "arguments",
    [["open", "--live"], ["open", "--seat", "remote"], ["show"], ["hide"]],
)
def test_what_only_the_avatar_host_offers_goes_to_the_host(this_mac, arguments):
    assert mac_talk.carry_out(arguments) == 7
    this_mac.host.assert_called_once_with(arguments)


@pytest.mark.parametrize("arguments", [["say", "hello"], ["status"], ["close"]])
def test_a_conversation_seated_through_the_host_keeps_its_verbs_there(
    this_mac, arguments
):
    this_mac.tunnel = {"attached": True, "listening": True}
    assert mac_talk.carry_out(arguments) == 7


def test_a_seat_the_host_stopped_using_does_not_draw_speech_to_the_host(this_mac):
    this_mac.tunnel = {"attached": True, "listening": False}
    assert mac_talk.carry_out(["say", "Good evening"]) == 0
    assert not this_mac.host.called


def test_opening_here_leaves_a_seat_the_host_stopped_using(this_mac, tmp_path):
    this_mac.tunnel = {"attached": True, "listening": False}
    mac_talk.open_conversation(OPENING, tmp_path)
    this_mac.leave.assert_called_once_with()


def test_a_seat_kept_for_a_meeting_is_left_alone(this_mac, tmp_path):
    this_mac.tunnel = {"attached": True, "listening": False, "meeting": True}
    mac_talk.open_conversation(OPENING, tmp_path)
    assert not this_mac.leave.called


def test_speech_stays_on_this_mac_when_no_host_conversation_is_seated(this_mac):
    assert mac_talk.carry_out(["say", "Good evening"]) == 0
    assert not this_mac.host.called
    assert this_mac.played == [b"pcm"]


def test_a_closed_conversation_still_speaks_through_the_speakers(this_mac, tmp_path):
    this_mac.attached = False
    mac_talk.speak(SPEECH, tmp_path)
    assert this_mac.played_without_a_seat == ["speech.wav"]
    assert this_mac.played == []


def test_the_holder_of_the_room_lends_its_voice(this_mac, tmp_path):
    conversation_addressee.hand_to(tmp_path, Addressee("w1:p1", "Sasaki Kojirou", 0))
    mac_talk.speak(SPEECH, tmp_path)
    assert this_mac.synthesized == [("Good evening", "neutral", "Sasaki Kojirou")]


def test_a_session_the_room_did_not_turn_to_may_not_speak(
    this_mac, tmp_path, monkeypatch
):
    conversation_addressee.hand_to(tmp_path, Addressee("w1:p1", "Sasaki Kojirou", 0))
    monkeypatch.setenv("HERDR_PANE_ID", "w9:p9")
    with pytest.raises(RuntimeError, match="holds the room"):
        mac_talk.speak(SPEECH, tmp_path)
    assert this_mac.synthesized == []


def test_an_opening_whose_page_never_attaches_leaves_nothing_running(
    this_mac, tmp_path, monkeypatch
):
    this_mac.attached = False
    monkeypatch.setattr(mac_talk, "ATTACH_WAIT_SECONDS", -1)
    with pytest.raises(TimeoutError, match="did not attach"):
        mac_talk.open_conversation(OPENING, tmp_path)
    this_mac.stop.assert_called_once_with()
    this_mac.close_browser.assert_called_once_with()


def test_opening_listens_with_barge_in_and_reports_the_conversation(
    this_mac, tmp_path, capsys
):
    mac_talk.open_conversation(OPENING, tmp_path)
    assert this_mac.begin.call_args.kwargs == {"language": "en", "barge_in": True}
    assert json.loads(capsys.readouterr().out)["open"] is True


def test_closing_leaves_no_record_of_what_was_said(this_mac, tmp_path, capsys):
    for record in mac_talk.PRIVATE_RECORDS:
        (tmp_path / record).write_text("private")
    conversation_addressee.hand_to(tmp_path, Addressee("w1:p1", "Sasaki Kojirou", 0))
    mac_talk.close_conversation(SimpleNamespace(), tmp_path)
    assert [path.name for path in tmp_path.iterdir() if path.is_file()] == [
        conversation_addressee.LOCK_FILE
    ]
    assert json.loads(capsys.readouterr().out) == {"open": False}


def test_hearing_a_closed_conversation_is_refused(this_mac, monkeypatch, tmp_path):
    this_mac.phase = ConversationPhase.CLOSED
    monkeypatch.setattr(
        mac_talk.listener_runtime, "runtime_directory", lambda: tmp_path
    )
    with pytest.raises(mac_talk.utterances.ConversationClosed):
        mac_talk.carry_out(["hear"])
