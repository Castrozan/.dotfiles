import json
from unittest.mock import Mock

import conversation_addressee
import conversation_effects
import conversation_state
import listener_session
import live_opening
import pytest
import remote_agent
import talk_cli
from meetings import start
from conversation_addressee import Addressee
from conversation_state import ConversationCommand, ConversationPhase
from talk_runner import run_talk


def test_opening_live_needs_the_agent_pane_that_will_receive_the_tasks(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.CLOSED
    )
    monkeypatch.delenv(remote_agent.PANE_ENVIRONMENT_VARIABLE, raising=False)
    bring_up = Mock()
    monkeypatch.setattr(start, "bring_up", bring_up)
    with pytest.raises(SystemExit):
        run_talk(monkeypatch, tmp_path, "open", "--live")
    bring_up.assert_not_called()
    assert live_opening.LIVE_NEEDS_A_PANE in capsys.readouterr().err


def test_opening_live_listens_for_the_live_voice_then_claims_the_floor(
    tmp_path, monkeypatch, capsys
):
    phases = iter([ConversationPhase.CLOSED, ConversationPhase.LIVE])
    monkeypatch.setattr(conversation_state, "observe", lambda directory: next(phases))
    monkeypatch.setenv(remote_agent.PANE_ENVIRONMENT_VARIABLE, "wW:pPT")
    steps = []
    monkeypatch.setattr(start, "bring_up", lambda *arguments: steps.append("bring-up"))
    monkeypatch.setattr(
        listener_session,
        "begin_listening",
        lambda directory, purpose, sources, **settings: steps.append(purpose),
    )

    def claim_floor(command, **options):
        steps.append(command[0])
        conversation_addressee.hand_to(tmp_path, Addressee("wW:pPT", "Suzuka", 0))

    monkeypatch.setattr(conversation_effects.subprocess, "run", claim_floor)
    run_talk(monkeypatch, tmp_path, "open", "--live")
    assert steps == [
        "bring-up",
        listener_session.ListenerPurpose.LIVE,
        "avatar-claim-floor",
    ]
    assert json.loads(capsys.readouterr().out) == {
        "open": True,
        "live": True,
        "seat": "room",
        "last_heard": 0,
    }


def test_the_floor_goes_to_a_named_pane_of_this_machine_not_the_calling_pane(
    tmp_path, monkeypatch
):
    monkeypatch.setenv(remote_agent.HOST_ENVIRONMENT_VARIABLE, "chise")
    monkeypatch.setenv(remote_agent.PANE_ENVIRONMENT_VARIABLE, "wW:pPT")
    handed = Mock()
    monkeypatch.setattr(live_opening.speaking_floor, "hand_to_remote_agent", handed)
    named = remote_agent.parse("chise:wW:pSP")
    live_opening.give_the_floor(tmp_path, named)
    handed.assert_called_once_with(tmp_path, remote_agent.AgentPane(None, "wW:pSP"))


@pytest.mark.parametrize("verb", [["ask", "oi"], ["hear"], ["follow"], ["say", "oi"]])
def test_the_desk_verbs_refuse_while_the_live_voice_owns_the_turns(
    tmp_path, monkeypatch, capsys, verb
):
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.LIVE
    )
    with pytest.raises(SystemExit):
        run_talk(monkeypatch, tmp_path, *verb)
    assert conversation_effects.LIVE_OWNS_THE_TURNS in capsys.readouterr().err


def test_opening_live_fails_and_closes_when_the_floor_cannot_name_the_opener(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.CLOSED
    )
    monkeypatch.setenv(remote_agent.PANE_ENVIRONMENT_VARIABLE, "wW:p00")
    monkeypatch.setattr(start, "bring_up", Mock())
    monkeypatch.setattr(listener_session, "begin_listening", Mock())
    monkeypatch.setattr(conversation_effects.subprocess, "run", Mock())
    close = Mock()
    monkeypatch.setattr(conversation_effects, "close_conversation", close)
    with pytest.raises(SystemExit):
        run_talk(monkeypatch, tmp_path, "open", "--live")
    close.assert_called_once()
    assert live_opening.LIVE_NEEDS_A_SERVANT in capsys.readouterr().err


def test_opening_live_over_an_open_conversation_refuses_and_leaves_it_running(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.OPEN
    )
    monkeypatch.setenv(remote_agent.PANE_ENVIRONMENT_VARIABLE, "wW:pSP")
    bring_up = Mock()
    close = Mock()
    monkeypatch.setattr(start, "bring_up", bring_up)
    monkeypatch.setattr(conversation_effects, "close_conversation", close)
    with pytest.raises(SystemExit):
        run_talk(monkeypatch, tmp_path, "open", "--live")
    bring_up.assert_not_called()
    close.assert_not_called()
    assert (
        capsys.readouterr().err.strip()
        == conversation_effects.CONVERSATION_OWNS_THE_ROOM
    )


def test_every_avatar_talk_command_in_every_phase_has_a_handler():
    talk_commands = set(ConversationCommand) - {ConversationCommand.TRANSCRIBE_MEETING}
    for phase in ConversationPhase:
        for command in talk_commands:
            assert conversation_state.decide(phase, command) in talk_cli.ACTIONS
