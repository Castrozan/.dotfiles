import json
from unittest.mock import Mock

import conversation_addressee
import conversation_effects
import conversation_state
import listener_session
import pytest
import start
from conversation_addressee import Addressee
from conversation_state import ConversationPhase
from talk_runner import run_talk


def test_opening_live_needs_the_agent_pane_that_will_receive_the_tasks(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.CLOSED
    )
    monkeypatch.delenv(conversation_effects.PANE_ENVIRONMENT_VARIABLE, raising=False)
    bring_up = Mock()
    monkeypatch.setattr(start, "bring_up", bring_up)
    with pytest.raises(SystemExit):
        run_talk(monkeypatch, tmp_path, "open", "--live")
    bring_up.assert_not_called()
    assert conversation_effects.LIVE_NEEDS_A_PANE in capsys.readouterr().err


def test_opening_live_listens_for_the_live_voice_then_claims_the_floor(
    tmp_path, monkeypatch, capsys
):
    phases = iter([ConversationPhase.CLOSED, ConversationPhase.LIVE])
    monkeypatch.setattr(conversation_state, "observe", lambda directory: next(phases))
    monkeypatch.setenv(conversation_effects.PANE_ENVIRONMENT_VARIABLE, "wW:pPT")
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
    monkeypatch.setenv(conversation_effects.PANE_ENVIRONMENT_VARIABLE, "wW:p00")
    monkeypatch.setattr(start, "bring_up", Mock())
    monkeypatch.setattr(listener_session, "begin_listening", Mock())
    monkeypatch.setattr(conversation_effects.subprocess, "run", Mock())
    close = Mock()
    monkeypatch.setattr(conversation_effects, "close_conversation", close)
    with pytest.raises(SystemExit):
        run_talk(monkeypatch, tmp_path, "open", "--live")
    close.assert_called_once()
    assert conversation_effects.LIVE_NEEDS_A_SERVANT in capsys.readouterr().err
