from listener_session import ListenerPurpose

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
