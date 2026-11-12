import argparse
from types import SimpleNamespace
from unittest.mock import Mock

import conversation_seat
import conversation_state
import pytest
import conversation_effects
import utterances
import voice_turns
from conversation_seat import Seat
from conversation_state import ConversationPhase
from talk_runner import run_talk


def test_the_window_appears_only_when_the_agent_shows_it(tmp_path, monkeypatch):
    show = Mock()
    hide = Mock()
    runner = Mock()
    monkeypatch.setattr(conversation_effects.desktop_window, "show", show)
    monkeypatch.setattr(conversation_effects.desktop_window, "hide", hide)
    monkeypatch.setattr(voice_turns.subprocess, "run", runner)
    monkeypatch.setattr(conversation_seat, "current", lambda directory: Seat.ROOM)
    conversation_effects.show_window(argparse.Namespace(), tmp_path)
    conversation_effects.hide_window(argparse.Namespace(), tmp_path)
    show.assert_called_once_with()
    hide.assert_called_once_with()
    assert [call.args[0][2] for call in runner.call_args_list] == ["shown", "hidden"]


def test_a_remote_seat_keeps_the_window_off_this_desktop(tmp_path, monkeypatch):
    show = Mock()
    runner = Mock()
    monkeypatch.setattr(conversation_effects.desktop_window, "show", show)
    monkeypatch.setattr(voice_turns.subprocess, "run", runner)
    monkeypatch.setattr(conversation_seat, "current", lambda directory: Seat.REMOTE)
    conversation_effects.show_window(argparse.Namespace(), tmp_path)
    show.assert_not_called()
    assert runner.call_args.args[0][1:] == ["presence", "shown"]


def test_showing_the_window_needs_an_open_conversation(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.CLOSED
    )
    show = Mock()
    monkeypatch.setattr(conversation_effects.desktop_window, "show", show)
    with pytest.raises(SystemExit):
        run_talk(monkeypatch, tmp_path, "show")
    show.assert_not_called()
    assert capsys.readouterr().err == utterances.CLOSED_MESSAGE + "\n"


def test_asking_speaks_and_prints_only_the_reply_tagged_as_voice(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.OPEN
    )
    runner = Mock()
    monkeypatch.setattr(voice_turns.subprocess, "run", runner)
    monkeypatch.setattr(utterances, "next_utterance", lambda *_: "tudo certo")
    voice_turns.ask(
        argparse.Namespace(
            language=None, text="Oi", emotion="happy", voice=None, wait=1
        ),
        tmp_path,
    )
    assert runner.call_args.args[0][:4] == ["avatar-command", "speak", "Oi", "happy"]
    assert runner.call_args.kwargs["stdout"] == voice_turns.subprocess.DEVNULL
    assert capsys.readouterr().out == "[voice] tudo certo\n"


def test_asking_after_the_user_closed_the_window_never_reopens_it(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.CLOSED
    )
    runner = Mock()
    monkeypatch.setattr(voice_turns.subprocess, "run", runner)
    with pytest.raises(SystemExit):
        run_talk(monkeypatch, tmp_path, "ask", "Oi")
    runner.assert_not_called()


@pytest.mark.parametrize(
    ("seat", "output"), [(Seat.ROOM, "speakers"), (Seat.REMOTE, "remote")]
)
def test_saying_plays_where_the_conversation_is_seated(
    tmp_path, monkeypatch, seat, output
):
    runner = Mock(return_value=SimpleNamespace(returncode=0))
    monkeypatch.setattr(voice_turns.subprocess, "run", runner)
    monkeypatch.setattr(conversation_seat, "current", lambda directory: seat)
    with pytest.raises(SystemExit):
        voice_turns.say(
            argparse.Namespace(text="oi", emotion="happy", voice=None), tmp_path
        )
    runner.assert_called_once_with(
        ["avatar-command", "speak", "oi", "happy", output],
        timeout=voice_turns.SPEECH_TIMEOUT_SECONDS,
    )
