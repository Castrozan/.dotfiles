import argparse
import json
import threading
from unittest.mock import Mock

import listen_cli
import listener
import pytest
import start
import talk_cli
import transcript_log
import utterances


def always_open():
    return True


def test_silence_returns_nothing_and_keeps_the_place(tmp_path):
    assert utterances.next_utterance(tmp_path, 0, always_open) is None
    assert utterances.last_heard(tmp_path) == 0


def test_hearing_consumes_everything_said_since_the_last_turn(tmp_path, monkeypatch):
    monkeypatch.setattr(utterances, "SETTLE_SECONDS", 0)
    path = tmp_path / "transcript.jsonl"
    transcript_log.append(path, "human", "primeira parte")
    transcript_log.append(path, "human", "segunda parte")
    assert (
        utterances.next_utterance(tmp_path, 0, always_open)
        == "primeira parte segunda parte"
    )
    assert utterances.next_utterance(tmp_path, 0, always_open) is None


def test_hearing_waits_while_the_human_is_still_talking(tmp_path, monkeypatch):
    monkeypatch.setattr(utterances, "SETTLE_SECONDS", 0)
    monkeypatch.setattr(utterances, "POLL_SECONDS", 0.01)
    path = tmp_path / "transcript.jsonl"
    marker = tmp_path / listener.SPEECH_IN_PROGRESS_MARKER
    transcript_log.append(path, "human", "antes da pausa")
    marker.touch()

    def finish_speaking():
        transcript_log.append(path, "human", "depois da pausa")
        marker.unlink()

    threading.Timer(0.05, finish_speaking).start()
    assert (
        utterances.next_utterance(tmp_path, 0, always_open)
        == "antes da pausa depois da pausa"
    )


def test_a_closed_conversation_ends_the_wait_instead_of_hanging(tmp_path):
    with pytest.raises(utterances.ConversationClosed):
        utterances.next_utterance(tmp_path, 60, lambda: False)


def test_opening_again_keeps_the_conversation_and_what_was_not_heard(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(talk_cli, "conversation_open", lambda: True)
    bring_up = Mock()
    monkeypatch.setattr(start, "bring_up", bring_up)
    utterances.remember(tmp_path, 7)
    talk_cli.open_conversation(
        argparse.Namespace(language=None, character=None), tmp_path
    )
    bring_up.assert_not_called()
    assert json.loads(capsys.readouterr().out) == {"open": True, "last_heard": 7}


def test_opening_refuses_to_replace_a_meeting_transcript(tmp_path, monkeypatch):
    monkeypatch.setattr(talk_cli, "conversation_open", lambda: False)
    monkeypatch.setattr(listen_cli, "listening", lambda: True)
    (tmp_path / "listener.json").write_text(
        json.dumps({"sources": {"meeting": "@DEFAULT_MONITOR@", "human": "mic"}})
    )
    begin = Mock()
    monkeypatch.setattr(listen_cli, "begin_listening", begin)
    with pytest.raises(RuntimeError):
        talk_cli.open_conversation(
            argparse.Namespace(language=None, character=None), tmp_path
        )
    begin.assert_not_called()


def test_opening_replaces_a_conversation_listener_left_running(tmp_path, monkeypatch):
    monkeypatch.setattr(talk_cli, "conversation_open", lambda: False)
    monkeypatch.setattr(listen_cli, "listening", lambda: True)
    (tmp_path / "listener.json").write_text(
        json.dumps({"sources": {"human": "AvatarRoomMicrophone"}})
    )
    monkeypatch.setattr(start, "bring_up", Mock())
    begin = Mock()
    monkeypatch.setattr(listen_cli, "begin_listening", begin)
    monkeypatch.setattr(talk_cli.subprocess, "run", Mock())
    talk_cli.open_conversation(
        argparse.Namespace(language="pt", character=None), tmp_path
    )
    begin.assert_called_once()


def test_opening_listens_only_to_the_cancelled_microphone(tmp_path, monkeypatch):
    monkeypatch.setattr(talk_cli, "conversation_open", lambda: False)
    monkeypatch.setattr(listen_cli, "listening", lambda: False)
    monkeypatch.setattr(start, "bring_up", Mock())
    begin = Mock()
    monkeypatch.setattr(listen_cli, "begin_listening", begin)
    runner = Mock()
    monkeypatch.setattr(talk_cli.subprocess, "run", runner)
    utterances.remember(tmp_path, 7)
    talk_cli.open_conversation(
        argparse.Namespace(language="pt", character=None), tmp_path
    )
    commands = [call.args[0] for call in runner.call_args_list]
    assert ["avatar-command", "presence", "shown"] not in commands
    begin.assert_called_once_with(
        tmp_path, {"human": "AvatarRoomMicrophone"}, language="pt", barge_in=True
    )
    assert utterances.last_heard(tmp_path) == 0


def test_a_failed_open_closes_what_it_started(tmp_path, monkeypatch):
    monkeypatch.setattr(talk_cli, "conversation_open", lambda: False)
    monkeypatch.setattr(listen_cli, "listening", lambda: False)
    monkeypatch.setattr(start, "bring_up", Mock(side_effect=TimeoutError("late")))
    close = Mock()
    monkeypatch.setattr(talk_cli, "close_conversation", close)
    with pytest.raises(TimeoutError):
        talk_cli.open_conversation(
            argparse.Namespace(language=None, character=None), tmp_path
        )
    close.assert_called_once()


@pytest.mark.parametrize(
    ("meeting_running", "stops_everything"), [(False, True), (True, False)]
)
def test_closing_leaves_a_running_meeting_alone(
    tmp_path, monkeypatch, meeting_running, stops_everything
):
    runner = Mock()
    monkeypatch.setattr(talk_cli.subprocess, "run", runner)
    hide = Mock()
    monkeypatch.setattr(talk_cli.desktop_window, "hide", hide)
    monkeypatch.setattr(
        talk_cli.user_units, "unit_active", lambda unit: meeting_running
    )
    talk_cli.close_conversation(argparse.Namespace(), tmp_path)
    commands = [call.args[0] for call in runner.call_args_list]
    assert ["systemctl", "--user", "stop", "avatar-conversation.target"] in commands
    assert (["avatar-stop"] in commands) is stops_everything
    hides_canvas = ["avatar-command", "presence", "hidden"] in commands
    assert hides_canvas is not stops_everything
    assert hide.called is not stops_everything
