import time

from conversation_seat import Seat
from listener_session import ListenerPurpose

ARM_CHECK_SECONDS = 5
TRANSCRIPT_POLL_SECONDS = 0.2
QUIET_CLOSE_SECONDS = 600
CLOSING = "closing a conversation the avatar has not spoken in for ten minutes"
CALL_ENDED = "closing the conversation because the listener left the Discord call"


def close_when_quiet(boundaries, dry_run=False):
    if dry_run or boundaries.quiet_seconds() < QUIET_CLOSE_SECONDS:
        return False
    if boundaries.listening_purpose() is not ListenerPurpose.CONVERSATION:
        return False
    boundaries.report(CLOSING)
    boundaries.close_conversation()
    return True


def close_when_the_call_ended(boundaries, dry_run=False):
    if dry_run or boundaries.open_seat() is not Seat.DISCORD:
        return False
    if not boundaries.discord_call_ended():
        return False
    boundaries.report(CALL_ENDED)
    boundaries.close_conversation()
    return True


def follow_conversation(wake):
    wake.start_reading_conversation()
    while True:
        check_at = time.monotonic() + ARM_CHECK_SECONDS
        while time.monotonic() < check_at:
            wake.read_conversation()
            time.sleep(TRANSCRIPT_POLL_SECONDS)
        if not wake.boundaries.conversation_listening():
            return
        if not close_when_the_call_ended(wake.boundaries, wake.dry_run):
            close_when_quiet(wake.boundaries, wake.dry_run)
