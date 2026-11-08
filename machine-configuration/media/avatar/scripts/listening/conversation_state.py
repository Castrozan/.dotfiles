import enum

import listener_session
import user_units
from listener_session import ListenerPurpose

CONVERSATION_TARGET = "avatar-conversation.target"


class ConversationPhase(enum.StrEnum):
    CLOSED = "closed"
    INTERRUPTED = "interrupted"
    OPEN = "open"
    MEETING = "meeting"


class ConversationCommand(enum.StrEnum):
    OPEN = "open"
    CLOSE = "close"
    ASK = "ask"
    HEAR = "hear"
    FOLLOW = "follow"
    SAY = "say"
    SHOW = "show"
    HIDE = "hide"
    STATUS = "status"
    TRANSCRIBE_MEETING = "transcribe-meeting"


class ConversationAction(enum.StrEnum):
    BRING_UP = "bring-up"
    KEEP_OPEN = "keep-open"
    TEAR_DOWN = "tear-down"
    LEAVE_MEETING = "leave-meeting"
    ASK = "ask"
    HEAR = "hear"
    FOLLOW = "follow"
    SAY = "say"
    SHOW = "show"
    HIDE = "hide"
    REPORT = "report"
    TRANSCRIBE_MEETING = "transcribe-meeting"
    REFUSE_CLOSED = "refuse-closed"
    REFUSE_MEETING = "refuse-meeting"
    REFUSE_CONVERSATION = "refuse-conversation"


PHASE_BY_TARGET_AND_PURPOSE = {
    (False, None): ConversationPhase.CLOSED,
    (False, ListenerPurpose.CONVERSATION): ConversationPhase.CLOSED,
    (False, ListenerPurpose.MEETING): ConversationPhase.MEETING,
    (True, None): ConversationPhase.INTERRUPTED,
    (True, ListenerPurpose.CONVERSATION): ConversationPhase.OPEN,
    (True, ListenerPurpose.MEETING): ConversationPhase.MEETING,
}

ACTIONS_WHEN_NOT_OPEN = {
    ConversationCommand.ASK: ConversationAction.REFUSE_CLOSED,
    ConversationCommand.HEAR: ConversationAction.REFUSE_CLOSED,
    ConversationCommand.FOLLOW: ConversationAction.REFUSE_CLOSED,
    ConversationCommand.SAY: ConversationAction.SAY,
    ConversationCommand.SHOW: ConversationAction.REFUSE_CLOSED,
    ConversationCommand.HIDE: ConversationAction.HIDE,
    ConversationCommand.STATUS: ConversationAction.REPORT,
}

TRANSITIONS = {
    ConversationPhase.CLOSED: ACTIONS_WHEN_NOT_OPEN
    | {
        ConversationCommand.OPEN: ConversationAction.BRING_UP,
        ConversationCommand.CLOSE: ConversationAction.TEAR_DOWN,
        ConversationCommand.TRANSCRIBE_MEETING: ConversationAction.TRANSCRIBE_MEETING,
    },
    ConversationPhase.INTERRUPTED: ACTIONS_WHEN_NOT_OPEN
    | {
        ConversationCommand.OPEN: ConversationAction.BRING_UP,
        ConversationCommand.CLOSE: ConversationAction.TEAR_DOWN,
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
    ConversationPhase.MEETING: ACTIONS_WHEN_NOT_OPEN
    | {
        ConversationCommand.OPEN: ConversationAction.REFUSE_MEETING,
        ConversationCommand.CLOSE: ConversationAction.LEAVE_MEETING,
        ConversationCommand.TRANSCRIBE_MEETING: ConversationAction.TRANSCRIBE_MEETING,
    },
}


def phase_of(target_active, live_purpose):
    return PHASE_BY_TARGET_AND_PURPOSE[(target_active, live_purpose)]


def observe(directory):
    return phase_of(
        user_units.unit_active(CONVERSATION_TARGET),
        listener_session.live_purpose(directory),
    )


def decide(phase, command):
    return TRANSITIONS[phase][command]
