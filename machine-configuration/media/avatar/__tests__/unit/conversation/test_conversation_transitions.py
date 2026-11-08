import itertools
from unittest.mock import Mock

import conversation_state
import conversation_effects
from conversation_state import (
    ConversationAction,
    ConversationCommand,
    ConversationPhase,
)
from listener_session import ListenerPurpose
from conversation_effects import WindowPresence

EXPECTED_TRANSITIONS = {
    ConversationPhase.CLOSED: {
        ConversationCommand.OPEN: ConversationAction.BRING_UP,
        ConversationCommand.CLOSE: ConversationAction.TEAR_DOWN,
        ConversationCommand.ASK: ConversationAction.REFUSE_CLOSED,
        ConversationCommand.HEAR: ConversationAction.REFUSE_CLOSED,
        ConversationCommand.FOLLOW: ConversationAction.REFUSE_CLOSED,
        ConversationCommand.SAY: ConversationAction.SAY,
        ConversationCommand.SHOW: ConversationAction.REFUSE_CLOSED,
        ConversationCommand.HIDE: ConversationAction.HIDE,
        ConversationCommand.STATUS: ConversationAction.REPORT,
        ConversationCommand.TRANSCRIBE_MEETING: ConversationAction.TRANSCRIBE_MEETING,
    },
    ConversationPhase.INTERRUPTED: {
        ConversationCommand.OPEN: ConversationAction.BRING_UP,
        ConversationCommand.CLOSE: ConversationAction.TEAR_DOWN,
        ConversationCommand.ASK: ConversationAction.REFUSE_CLOSED,
        ConversationCommand.HEAR: ConversationAction.REFUSE_CLOSED,
        ConversationCommand.FOLLOW: ConversationAction.REFUSE_CLOSED,
        ConversationCommand.SAY: ConversationAction.SAY,
        ConversationCommand.SHOW: ConversationAction.REFUSE_CLOSED,
        ConversationCommand.HIDE: ConversationAction.HIDE,
        ConversationCommand.STATUS: ConversationAction.REPORT,
        ConversationCommand.TRANSCRIBE_MEETING: ConversationAction.REFUSE_CONVERSATION,
    },
    ConversationPhase.OPEN: {
        ConversationCommand.OPEN: ConversationAction.KEEP_OPEN,
        ConversationCommand.CLOSE: ConversationAction.TEAR_DOWN,
        ConversationCommand.ASK: ConversationAction.ASK,
        ConversationCommand.HEAR: ConversationAction.HEAR,
        ConversationCommand.FOLLOW: ConversationAction.FOLLOW,
        ConversationCommand.SAY: ConversationAction.SAY,
        ConversationCommand.SHOW: ConversationAction.SHOW,
        ConversationCommand.HIDE: ConversationAction.HIDE,
        ConversationCommand.STATUS: ConversationAction.REPORT,
        ConversationCommand.TRANSCRIBE_MEETING: ConversationAction.REFUSE_CONVERSATION,
    },
    ConversationPhase.MEETING: {
        ConversationCommand.OPEN: ConversationAction.REFUSE_MEETING,
        ConversationCommand.CLOSE: ConversationAction.LEAVE_MEETING,
        ConversationCommand.ASK: ConversationAction.REFUSE_CLOSED,
        ConversationCommand.HEAR: ConversationAction.REFUSE_CLOSED,
        ConversationCommand.FOLLOW: ConversationAction.REFUSE_CLOSED,
        ConversationCommand.SAY: ConversationAction.SAY,
        ConversationCommand.SHOW: ConversationAction.REFUSE_CLOSED,
        ConversationCommand.HIDE: ConversationAction.HIDE,
        ConversationCommand.STATUS: ConversationAction.REPORT,
        ConversationCommand.TRANSCRIBE_MEETING: ConversationAction.TRANSCRIBE_MEETING,
    },
}

EXPECTED_PHASE_BY_TARGET_AND_PURPOSE = {
    (False, None): ConversationPhase.CLOSED,
    (False, ListenerPurpose.CONVERSATION): ConversationPhase.CLOSED,
    (False, ListenerPurpose.MEETING): ConversationPhase.MEETING,
    (True, None): ConversationPhase.INTERRUPTED,
    (True, ListenerPurpose.CONVERSATION): ConversationPhase.OPEN,
    (True, ListenerPurpose.MEETING): ConversationPhase.MEETING,
}


def test_the_transition_table_decides_every_phase_and_command_as_pinned():
    decided_cells = {
        (phase, command)
        for phase in conversation_state.TRANSITIONS
        for command in conversation_state.TRANSITIONS[phase]
    }
    assert decided_cells == set(
        itertools.product(ConversationPhase, ConversationCommand)
    )
    assert conversation_state.TRANSITIONS == EXPECTED_TRANSITIONS


def test_the_phase_of_every_target_and_purpose_pair_is_pinned():
    purposes = (None, *ListenerPurpose)
    assert set(conversation_state.PHASE_BY_TARGET_AND_PURPOSE) == set(
        itertools.product((True, False), purposes)
    )
    assert (
        conversation_state.PHASE_BY_TARGET_AND_PURPOSE
        == EXPECTED_PHASE_BY_TARGET_AND_PURPOSE
    )


def test_the_canvas_and_the_window_follow_the_stated_order_for_every_presence(
    monkeypatch,
):
    steps = []
    monkeypatch.setattr(
        conversation_effects.subprocess,
        "run",
        Mock(side_effect=lambda *a, **k: steps.append("canvas")),
    )
    monkeypatch.setattr(
        conversation_effects.desktop_window, "show", lambda: steps.append("window")
    )
    monkeypatch.setattr(
        conversation_effects.desktop_window, "hide", lambda: steps.append("window")
    )
    orders = {}
    for presence in WindowPresence:
        steps.clear()
        conversation_effects.apply_presence(presence)
        orders[presence] = list(steps)
    assert orders == {
        WindowPresence.HIDDEN: ["canvas", "window"],
        WindowPresence.SHOWN: ["window", "canvas"],
    }
