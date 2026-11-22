import os

import conversation_addressee
import listener_session
import mac_stage
import remote_agent
import utterances
import voice_turns
from conversation_seat import Seat

ROOM_HELD_ELSEWHERE = "Another session holds the room; it speaks until the room turns"


def refuse_unless_addressed(directory):
    pane = os.environ.get(remote_agent.PANE_ENVIRONMENT_VARIABLE)
    if not conversation_addressee.addresses(directory, pane):
        raise RuntimeError(ROOM_HELD_ELSEWHERE)


def speak(arguments, directory):
    refuse_unless_addressed(directory)
    listener_session.mark_spoken(directory)
    with mac_stage.standing():
        mac_stage.speak(arguments.text, arguments.emotion, arguments.voice)


def speech_in_turn(arguments, directory):
    refuse_unless_addressed(directory)
    listener_session.mark_spoken(directory)
    command = voice_turns.speech_command_on_seat(arguments, Seat.ROOM)
    with mac_stage.standing():
        return voice_turns.spoken_in_turn(command, directory)


def reply(arguments, directory):
    voice_turns.print_and_exit(speech_in_turn(arguments, directory))


def ask(arguments, directory):
    with utterances.exclusive_consumer(directory):
        completed = speech_in_turn(arguments, directory)
        voice_turns.listen_after(completed, directory, arguments.wait)
