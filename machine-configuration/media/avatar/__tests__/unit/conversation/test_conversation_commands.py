import argparse
import json
import sys
import threading
from unittest.mock import Mock

import conversation_state
import listener_session
import listener
import pytest
import start
import conversation_effects
import talk_cli
import transcript_log
import utterances
from conversation_state import ConversationPhase


def always_open():
    return True


def run_talk(monkeypatch, directory, *arguments):
    monkeypatch.setattr(sys, "argv", ["avatar-talk", *arguments])
    monkeypatch.setattr(talk_cli.listener, "runtime_directory", lambda: directory)
    talk_cli.main()


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
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.OPEN
    )
    bring_up = Mock()
    monkeypatch.setattr(start, "bring_up", bring_up)
    utterances.remember(tmp_path, 7)
    run_talk(monkeypatch, tmp_path, "open")
    bring_up.assert_not_called()
    assert json.loads(capsys.readouterr().out) == {"open": True, "last_heard": 7}


def test_opening_refuses_to_replace_a_meeting_transcript(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.MEETING
    )
    bring_up = Mock()
    monkeypatch.setattr(start, "bring_up", bring_up)
    begin = Mock()
    monkeypatch.setattr(listener_session, "begin_listening", begin)
    with pytest.raises(SystemExit):
        run_talk(monkeypatch, tmp_path, "open")
    bring_up.assert_not_called()
    begin.assert_not_called()
    assert "A meeting is being transcribed" in capsys.readouterr().err


def test_closing_during_a_meeting_touches_no_unit_and_reports_closed(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.MEETING
    )
    runner = Mock()
    monkeypatch.setattr(conversation_effects.subprocess, "run", runner)
    run_talk(monkeypatch, tmp_path, "close")
    runner.assert_not_called()
    assert json.loads(capsys.readouterr().out) == {"open": False}


def test_opening_replaces_a_conversation_listener_left_running(tmp_path, monkeypatch):
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.CLOSED
    )
    monkeypatch.setattr(listener_session, "listening", lambda: True)
    (tmp_path / "listener.json").write_text(
        json.dumps(
            {"purpose": "conversation", "sources": {"human": "AvatarRoomMicrophone"}}
        )
    )
    monkeypatch.setattr(start, "bring_up", Mock())
    begin = Mock()
    monkeypatch.setattr(listener_session, "begin_listening", begin)
    monkeypatch.setattr(conversation_effects.subprocess, "run", Mock())
    conversation_effects.open_conversation(
        argparse.Namespace(language="pt", character=None), tmp_path
    )
    begin.assert_called_once()


def test_opening_listens_only_to_the_cancelled_microphone(tmp_path, monkeypatch):
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.CLOSED
    )
    monkeypatch.setattr(listener_session, "listening", lambda: False)
    monkeypatch.setattr(start, "bring_up", Mock())
    begin = Mock()
    monkeypatch.setattr(listener_session, "begin_listening", begin)
    runner = Mock()
    monkeypatch.setattr(conversation_effects.subprocess, "run", runner)
    conversation_effects.open_conversation(
        argparse.Namespace(language="pt", character=None), tmp_path
    )
    commands = [call.args[0] for call in runner.call_args_list]
    assert ["avatar-command", "presence", "shown"] not in commands
    begin.assert_called_once_with(
        tmp_path,
        listener_session.ListenerPurpose.CONVERSATION,
        {"human": "AvatarRoomMicrophone"},
        language="pt",
        barge_in=True,
    )


def test_a_failed_open_closes_what_it_started(tmp_path, monkeypatch):
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.CLOSED
    )
    monkeypatch.setattr(listener_session, "listening", lambda: False)
    monkeypatch.setattr(start, "bring_up", Mock(side_effect=TimeoutError("late")))
    close = Mock()
    monkeypatch.setattr(conversation_effects, "close_conversation", close)
    with pytest.raises(TimeoutError):
        conversation_effects.open_conversation(
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
    monkeypatch.setattr(conversation_effects.subprocess, "run", runner)
    hide = Mock()
    monkeypatch.setattr(conversation_effects.desktop_window, "hide", hide)
    monkeypatch.setattr(
        conversation_effects.user_units, "unit_active", lambda unit: meeting_running
    )
    conversation_effects.close_conversation(argparse.Namespace(), tmp_path)
    commands = [call.args[0] for call in runner.call_args_list]
    assert ["systemctl", "--user", "stop", "avatar-conversation.target"] in commands
    assert (["avatar-stop"] in commands) is stops_everything
    hides_canvas = ["avatar-command", "presence", "hidden"] in commands
    assert hides_canvas is not stops_everything
    assert hide.called is not stops_everything
