import json
from types import SimpleNamespace
from unittest.mock import Mock

import conversation_addressee
import conversation_effects
import conversation_seat
import conversation_state
import listener_session
import live_opening
import local_seat
import pytest
import remote_agent
import remote_talk
import start
from conversation_addressee import Addressee
from conversation_state import ConversationPhase
from talk_runner import run_talk


def run_main(monkeypatch, *arguments):
    monkeypatch.setattr(remote_talk.sys, "argv", ["avatar-talk", *arguments])
    with pytest.raises(SystemExit) as finished:
        remote_talk.main()
    return finished.value.code


def agent_session(monkeypatch, host="kira", pane="w4A:p1"):
    for name, value in (
        (remote_talk.HOST_ENVIRONMENT_VARIABLE, host),
        (remote_talk.PANE_ENVIRONMENT_VARIABLE, pane),
    ):
        if value is None:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, value)


@pytest.mark.parametrize(
    ("here", "forwarded"),
    [
        (True, "open --live --agent kira:w4A:p1 --seat remote"),
        (False, "open --live --agent kira:w4A:p1"),
    ],
)
def test_live_from_a_mac_names_the_agent_that_receives_the_tasks(
    monkeypatch, here, forwarded
):
    agent_session(monkeypatch)
    monkeypatch.setattr(remote_talk, "user_is_here", lambda: here)
    status = json.dumps({"open": True, "live": True, "seat": "room"})
    runner = Mock(return_value=SimpleNamespace(returncode=0, stdout=status))
    monkeypatch.setattr(remote_talk.subprocess, "run", runner)
    monkeypatch.setattr(local_seat, "take", Mock())
    assert run_main(monkeypatch, "open", "--live") == 0
    assert runner.call_args.args[0] == ["ssh", "chise", "avatar-talk", forwarded]


@pytest.mark.parametrize(("host", "pane"), [(None, "w4A:p1"), ("kira", None)])
def test_live_from_a_mac_without_an_agent_pane_is_refused_here(
    monkeypatch, capsys, host, pane
):
    agent_session(monkeypatch, host, pane)
    runner = Mock()
    monkeypatch.setattr(remote_talk.subprocess, "run", runner)
    assert run_main(monkeypatch, "open", "--live") == 1
    runner.assert_not_called()
    assert remote_talk.LIVE_NEEDS_A_PANE in capsys.readouterr().err


def opening_live_for_a_remote_agent(tmp_path, monkeypatch, servant):
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.CLOSED
    )
    monkeypatch.delenv(live_opening.PANE_ENVIRONMENT_VARIABLE, raising=False)
    monkeypatch.setattr(start, "bring_up", Mock())
    monkeypatch.setattr(conversation_seat, "prepare", Mock())
    listening = Mock()
    monkeypatch.setattr(listener_session, "begin_listening", listening)
    monkeypatch.setattr(remote_agent, "servant_at", lambda agent: servant)
    local_command = Mock()
    monkeypatch.setattr(live_opening.subprocess, "run", local_command)
    monkeypatch.setattr(conversation_effects, "status", Mock())
    close = Mock()
    monkeypatch.setattr(conversation_effects, "close_conversation", close)
    return listening, local_command, close


def test_live_for_an_agent_on_another_machine_gives_it_the_floor(tmp_path, monkeypatch):
    listening, local_command, close = opening_live_for_a_remote_agent(
        tmp_path, monkeypatch, "Sasaki Kojirou"
    )
    run_talk(
        monkeypatch,
        tmp_path,
        *("open", "--live", "--seat", "remote", "--agent", "kira:w4A:p1"),
    )
    assert conversation_addressee.current(tmp_path) == Addressee(
        "w4A:p1", "Sasaki Kojirou", 0, "kira"
    )
    assert listening.call_args.args[2] == {"human": "AvatarRemoteMicrophone.monitor"}
    assert listening.call_args.kwargs == {"seat": "remote"}
    conversation_seat.prepare.assert_called_once_with("remote")
    local_command.assert_not_called()
    close.assert_not_called()


def test_live_for_a_remote_pane_without_a_servant_fails_and_closes(
    tmp_path, monkeypatch, capsys
):
    _, _, close = opening_live_for_a_remote_agent(tmp_path, monkeypatch, None)
    with pytest.raises(SystemExit):
        run_talk(monkeypatch, tmp_path, "open", "--live", "--agent", "kira:w4A:p1")
    close.assert_called_once()
    assert live_opening.LIVE_NEEDS_A_SERVANT in capsys.readouterr().err
