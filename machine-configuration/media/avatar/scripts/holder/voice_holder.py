import subprocess
import sys
import time

import conversation_addressee
import conversation_seat
import conversation_state
import default_holder
import utterances
import voice_turns
from conversation_state import ConversationPhase
from hermes_turn import FAILED_TURN_APOLOGY, HermesTurnError, reply_worth_speaking

FLOOR_POLL_SECONDS = 1
OPEN_CHECK_SECONDS = 5


class FloorHolder:
    def __init__(self, directory, holder, reply_to, speak_on_seat):
        self.directory = directory
        self.holder = holder
        self.reply_to = reply_to
        self.speak_on_seat = speak_on_seat

    def still_open(self):
        return conversation_state.observe(self.directory) is ConversationPhase.OPEN

    def addressed(self):
        return conversation_addressee.addresses(self.directory, self.holder.pane)

    def hold(self):
        default_holder.take_the_floor(self.directory, self.holder)
        while True:
            if self.addressed():
                self.serve_while_addressed()
            else:
                self.wait_for_the_floor()

    def serve_while_addressed(self):
        try:
            with utterances.exclusive_consumer(self.directory):
                while self.addressed():
                    self.answer_next_utterance()
        except utterances.ConversationBusy:
            time.sleep(FLOOR_POLL_SECONDS)

    def answer_next_utterance(self):
        heard = utterances.next_utterance(
            self.directory,
            voice_turns.FOLLOW_SLICE_SECONDS,
            self.still_open,
            self.addressed,
        )
        if heard:
            self.answer(heard)

    def answer(self, heard):
        try:
            reply = self.reply_to(heard)
        except HermesTurnError as error:
            print(error, file=sys.stderr)
            reply = FAILED_TURN_APOLOGY
        if reply_worth_speaking(reply) and self.addressed():
            self.speak(reply)

    def speak(self, text):
        seat = conversation_seat.current(self.directory)
        try:
            self.speak_on_seat(self.directory, text, seat)
        except (OSError, subprocess.SubprocessError) as error:
            print(error, file=sys.stderr)

    def wait_for_the_floor(self):
        still_open = utterances.ThrottledCheck(self.still_open, OPEN_CHECK_SECONDS)
        while not self.addressed():
            if not still_open.passes():
                raise utterances.ConversationClosed(utterances.CLOSED_MESSAGE)
            time.sleep(FLOOR_POLL_SECONDS)
