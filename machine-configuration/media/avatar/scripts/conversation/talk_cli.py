import subprocess
import sys

import conversation_effects
import conversation_seat
import conversation_state
import listener_runtime
import live_opening
import room_reach
import utterances
import voice_turns
from conversation_state import ConversationAction, ConversationCommand
from talk_arguments import parse_arguments


def decision_for(arguments, directory):
    command = (
        ConversationCommand.OPEN_LIVE
        if getattr(arguments, "live", False)
        else ConversationCommand(arguments.action)
    )
    requested_seat = getattr(arguments, "seat", None)
    return conversation_state.decide(
        conversation_state.observe(directory),
        command,
        requested_seat,
        conversation_seat.configured(directory) if requested_seat else None,
    )


def main():
    forwarded = room_reach.forwarded_from_this_machine(sys.argv[1:])
    if forwarded is not None:
        sys.exit(forwarded)
    arguments = parse_arguments()
    actions = {
        ConversationAction.BRING_UP: conversation_effects.open_conversation,
        ConversationAction.BRING_UP_LIVE: live_opening.open_live_conversation,
        ConversationAction.KEEP_OPEN: conversation_effects.keep_conversation_open,
        ConversationAction.TEAR_DOWN: conversation_effects.close_conversation,
        ConversationAction.LEAVE_MEETING: conversation_effects.leave_meeting,
        ConversationAction.ASK: voice_turns.ask,
        ConversationAction.HEAR: voice_turns.hear,
        ConversationAction.FOLLOW: voice_turns.follow,
        ConversationAction.SAY: voice_turns.say,
        ConversationAction.SHOW: conversation_effects.show_window,
        ConversationAction.HIDE: conversation_effects.hide_window,
        ConversationAction.REPORT: conversation_effects.status,
        ConversationAction.REFUSE_CLOSED: conversation_effects.refuse_closed,
        ConversationAction.REFUSE_MEETING: conversation_effects.refuse_meeting,
        ConversationAction.REFUSE_LIVE: conversation_effects.refuse_live,
        ConversationAction.REFUSE_SEAT_CHANGE: conversation_effects.refuse_seat_change,
    }
    try:
        directory = listener_runtime.runtime_directory()
        actions[decision_for(arguments, directory)](arguments, directory)
    except (
        utterances.ConversationClosed,
        subprocess.SubprocessError,
        RuntimeError,
        TimeoutError,
        ValueError,
    ) as error:
        print(error, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
