import argparse
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import conversation_state
import pytest
import conversation_effects
import talk_cli
import utterances
from conversation_state import ConversationPhase


def run_talk(monkeypatch, directory, *arguments):
    monkeypatch.setattr(sys, "argv", ["avatar-talk", *arguments])
    monkeypatch.setattr(talk_cli.listener, "runtime_directory", lambda: directory)
    talk_cli.main()


def test_the_window_appears_only_when_the_agent_shows_it(tmp_path, monkeypatch):
    show = Mock()
    hide = Mock()
    runner = Mock()
    monkeypatch.setattr(conversation_effects.desktop_window, "show", show)
    monkeypatch.setattr(conversation_effects.desktop_window, "hide", hide)
    monkeypatch.setattr(conversation_effects.subprocess, "run", runner)
    conversation_effects.show_window(argparse.Namespace(), tmp_path)
    conversation_effects.hide_window(argparse.Namespace(), tmp_path)
    show.assert_called_once_with()
    hide.assert_called_once_with()
    assert [call.args[0][2] for call in runner.call_args_list] == ["shown", "hidden"]


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
    monkeypatch.setattr(conversation_effects.subprocess, "run", runner)
    monkeypatch.setattr(utterances, "next_utterance", lambda *_: "tudo certo")
    conversation_effects.ask(
        argparse.Namespace(
            language=None, text="Oi", emotion="happy", voice=None, wait=1
        ),
        tmp_path,
    )
    assert runner.call_args.args[0][:4] == ["avatar-command", "speak", "Oi", "happy"]
    assert runner.call_args.kwargs["stdout"] == conversation_effects.subprocess.DEVNULL
    assert capsys.readouterr().out == "[voice] tudo certo\n"


def test_asking_after_the_user_closed_the_window_never_reopens_it(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.CLOSED
    )
    runner = Mock()
    monkeypatch.setattr(conversation_effects.subprocess, "run", runner)
    with pytest.raises(SystemExit):
        run_talk(monkeypatch, tmp_path, "ask", "Oi")
    runner.assert_not_called()


def test_saying_plays_aloud_and_reports_the_speech_result(tmp_path, monkeypatch):
    runner = Mock(return_value=SimpleNamespace(returncode=0))
    monkeypatch.setattr(conversation_effects.subprocess, "run", runner)
    with pytest.raises(SystemExit):
        conversation_effects.say(
            argparse.Namespace(text="oi", emotion="happy", voice=None), tmp_path
        )
    runner.assert_called_once_with(
        ["avatar-command", "speak", "oi", "happy", "speakers"],
        timeout=conversation_effects.SPEECH_TIMEOUT_SECONDS,
    )
