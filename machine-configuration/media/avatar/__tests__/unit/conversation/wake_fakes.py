from unittest.mock import Mock

import wake_boundaries
import wake_listener
from listener_session import ListenerPurpose
from wake_phrase import LiveSession

VOYAGER = LiveSession("Voyager", "wW:pPZ")
IBARAKI = LiveSession("Ibaraki-dōji", "wW:pPY")


def boundaries(heard="hey Voyager, check the build", sessions=(VOYAGER,), **changes):
    fakes = dict(
        sessions=Mock(return_value=list(sessions)),
        conversation_listening=Mock(return_value=False),
        transcribe=Mock(return_value=heard),
        open_conversation=Mock(return_value=True),
        prompt_now=Mock(return_value=True),
        notify_at_idle=Mock(),
        report=Mock(),
        now=Mock(return_value=0.0),
        transcript_entries=Mock(return_value=[]),
        listening_purpose=Mock(return_value=ListenerPurpose.CONVERSATION),
        addressee=Mock(return_value=None),
        hand_to=Mock(),
    )
    fakes.update(changes)
    return wake_boundaries.Boundaries(**fakes)


def armed_listener(fakes, dry_run=False):
    listener = wake_listener.WakeListener(fakes, dry_run=dry_run)
    listener.armed()
    return listener
