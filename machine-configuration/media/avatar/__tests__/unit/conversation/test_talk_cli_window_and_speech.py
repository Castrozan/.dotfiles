import argparse
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import talk_cli
import utterances


def test_the_window_appears_only_when_the_agent_shows_it(tmp_path, monkeypatch):
    monkeypatch.setattr(talk_cli, "conversation_open", lambda directory: True)
    show = Mock()
    hide = Mock()
    runner = Mock()
    monkeypatch.setattr(talk_cli.desktop_window, "show", show)
    monkeypatch.setattr(talk_cli.desktop_window, "hide", hide)
    monkeypatch.setattr(talk_cli.subprocess, "run", runner)
    talk_cli.show_window(argparse.Namespace(), tmp_path)
    talk_cli.hide_window(argparse.Namespace(), tmp_path)
    show.assert_called_once_with()
    hide.assert_called_once_with()
    assert [call.args[0][2] for call in runner.call_args_list] == ["shown", "hidden"]


def test_showing_the_window_needs_an_open_conversation(tmp_path, monkeypatch):
    monkeypatch.setattr(talk_cli, "conversation_open", lambda directory: False)
    show = Mock()
    monkeypatch.setattr(talk_cli.desktop_window, "show", show)
    with pytest.raises(utterances.ConversationClosed):
        talk_cli.show_window(argparse.Namespace(), tmp_path)
    show.assert_not_called()


def test_asking_speaks_and_prints_only_the_reply_tagged_as_voice(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(talk_cli, "conversation_open", lambda directory: True)
    runner = Mock()
    monkeypatch.setattr(talk_cli.subprocess, "run", runner)
    monkeypatch.setattr(utterances, "next_utterance", lambda *_: "tudo certo")
    talk_cli.ask(
        argparse.Namespace(
            language=None, text="Oi", emotion="happy", voice=None, wait=1
        ),
        tmp_path,
    )
    assert runner.call_args.args[0][:4] == ["avatar-command", "speak", "Oi", "happy"]
    assert runner.call_args.kwargs["stdout"] == talk_cli.subprocess.DEVNULL
    assert capsys.readouterr().out == "[voice] tudo certo\n"


def test_asking_after_the_user_closed_the_window_never_reopens_it(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(talk_cli, "conversation_open", lambda directory: False)
    runner = Mock()
    monkeypatch.setattr(talk_cli.subprocess, "run", runner)
    with pytest.raises(utterances.ConversationClosed):
        talk_cli.ask(
            argparse.Namespace(text="Oi", emotion="neutral", voice=None, wait=1),
            tmp_path,
        )
    runner.assert_not_called()


def test_saying_plays_aloud_and_reports_the_speech_result(tmp_path, monkeypatch):
    runner = Mock(return_value=SimpleNamespace(returncode=0))
    monkeypatch.setattr(talk_cli.subprocess, "run", runner)
    with pytest.raises(SystemExit):
        talk_cli.say(
            argparse.Namespace(text="oi", emotion="happy", voice=None), tmp_path
        )
    runner.assert_called_once_with(
        ["avatar-command", "speak", "oi", "happy", "speakers"]
    )
