import time

from conversation_seat import Seat
from listener_session import ListenerPurpose

ARM_CHECK_SECONDS = 5
TRANSCRIPT_POLL_SECONDS = 0.2
QUIET_CLOSE_SECONDS = 600
MAX_TURN_CHARACTERS = 16_384
CLOSING = "closing a conversation the avatar has not spoken in for ten minutes"
CALL_ENDED = "closing the conversation because the listener left the Discord call"


class ConversationTranscript:
    def __init__(self):
        self.start(())

    def start(self, entries):
        self.read_through = entries[-1]["sequence"] if entries else 0
        self.reset_turn()

    def reset_turn(self):
        self.text = ""
        self.source = None
        self.speaker = None

    def new_entries(self, entries):
        if not entries or entries[-1]["sequence"] < self.read_through:
            self.start(())
        for entry in entries:
            if entry["sequence"] > self.read_through:
                self.read_through = entry["sequence"]
                yield entry

    def completed_turn(self, entry):
        speaker = entry.get("speaker")
        if speaker == "avatar":
            return None
        source = entry.get("source")
        if source != self.source or (
            speaker and self.speaker and speaker != self.speaker
        ):
            self.reset_turn()
        self.source = source
        self.speaker = speaker or self.speaker
        if self.text is not None:
            fragment = entry["text"]
            if len(self.text) + len(fragment) + bool(self.text) > MAX_TURN_CHARACTERS:
                self.text = None
            else:
                self.text = f"{self.text} {fragment}" if self.text else fragment
        if not entry.get("turn_finished", True):
            return None
        text = self.text
        self.reset_turn()
        return entry | {"text": text} if text is not None else None


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
