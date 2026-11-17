import time

from listener_session import ListenerPurpose

ARM_CHECK_SECONDS = 5
TRANSCRIPT_POLL_SECONDS = 0.2
QUIET_CLOSE_SECONDS = 600
CLOSING = "closing a conversation the avatar has not spoken in for ten minutes"


def close_when_quiet(boundaries, dry_run=False):
    if dry_run or boundaries.quiet_seconds() < QUIET_CLOSE_SECONDS:
        return False
    if boundaries.listening_purpose() is not ListenerPurpose.CONVERSATION:
        return False
    boundaries.report(CLOSING)
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
        close_when_quiet(wake.boundaries, wake.dry_run)
