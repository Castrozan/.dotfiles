from unittest.mock import Mock

import addressing_decision
import wake_boundaries
import wake_listener
from conversation_seat import Seat
from listener_session import ListenerPurpose
from wake_phrase import LiveSession

VOYAGER = LiveSession("Voyager", "wW:pPZ")
IBARAKI = LiveSession("Ibaraki-dōji", "wW:pPY")
UNREACHABLE = OSError("the Decisions API is unreachable")


def answered(choice, confidence=0.97):
    return [
        {
            "type": "choice",
            "name": addressing_decision.QUESTION,
            "choice": choice,
            "confidence": confidence,
        }
    ]


def deciding(decided):
    if isinstance(decided, Exception):
        return Mock(side_effect=decided)
    return Mock(return_value=decided)


def agreeing_with_the_named_servant(input_messages, questions):
    values = [choice["value"] for choice in questions[0]["choices"]]
    unnamed = {addressing_decision.HOLDER, addressing_decision.NOBODY}
    return answered(next(value for value in values if value not in unnamed))


def boundaries(heard="hey Voyager, check the build", sessions=(VOYAGER,), **changes):
    fakes = dict(
        sessions=Mock(return_value=list(sessions)),
        discord_call_host=Mock(return_value=None),
        conversation_listening=Mock(return_value=False),
        transcribe=Mock(return_value=heard),
        decide=Mock(side_effect=agreeing_with_the_named_servant),
        open_seat=Mock(return_value=Seat.ROOM),
        claim_wake=Mock(return_value=True),
        open_conversation=Mock(return_value=True),
        prompt_now=Mock(return_value=True),
        notify_at_idle=Mock(),
        report=Mock(),
        now=Mock(return_value=0.0),
        pause=Mock(),
        transcript_entries=Mock(return_value=[]),
        listening_purpose=Mock(return_value=ListenerPurpose.CONVERSATION),
        addressee=Mock(return_value=None),
        hand_to=Mock(),
        quiet_seconds=Mock(return_value=0.0),
        close_conversation=Mock(),
    )
    fakes.update(changes)
    return wake_boundaries.Boundaries(**fakes)


def armed_listener(fakes, dry_run=False):
    listener = wake_listener.WakeListener(fakes, dry_run=dry_run)
    listener.armed()
    return listener
