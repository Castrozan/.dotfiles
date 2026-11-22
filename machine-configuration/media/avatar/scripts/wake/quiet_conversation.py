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

    def spoken_by_another_voice(self, source, speaker):
        return source != self.source or bool(
            speaker and self.speaker and speaker != self.speaker
        )

    def append(self, fragment):
        if self.text is None:
            return
        joined = f"{self.text} {fragment}" if self.text else fragment
        self.text = joined if len(joined) <= MAX_TURN_CHARACTERS else None

    def extend_turn(self, entry):
        source = entry.get("source")
        speaker = entry.get("speaker")
        if self.spoken_by_another_voice(source, speaker):
            self.reset_turn()
        self.source = source
        self.speaker = speaker or self.speaker
        self.append(entry["text"])

    def completed_turn(self, entry):
        if entry.get("speaker") == "avatar":
            return None
        self.extend_turn(entry)
        if not entry.get("turn_finished", True):
            return None
        text = self.text
        self.reset_turn()
        return None if text is None else entry | {"text": text}


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
