import json
import os
import subprocess
import sys
import time

import conversation_addressee
import conversation_state
import listener
import listener_runtime
import listener_session
import local_seat
import mac_seat_client
import mac_speech
import remote_talk
import utterances
import voice_turns
from conversation_state import ConversationAction, ConversationCommand
from conversation_state import ConversationPhase
from listener_session import ListenerPurpose
from talk_arguments import parse_arguments

MICROPHONE = "the microphone of this Mac"
SEAT = "room"
ATTACH_WAIT_SECONDS = 25
POLL_SECONDS = 0.25
WINDOW_VERBS = ("show", "hide")
HOST_OPTIONS = ("--live", "--seat")
PRIVATE_RECORDS = ("transcript.jsonl", listener.EMBEDDINGS_FILE, listener.HEARD_FILE)
ROOM_HELD_ELSEWHERE = "Another session holds the room; it speaks until the room turns"
SEAT_DID_NOT_ATTACH = (
    f"The conversation page did not attach; check that {local_seat.BROWSER} "
    "may use the microphone"
)
VOICE_ONLY = "This Mac converses by voice alone; --character applies at the avatar host"
NOT_HERE = "This Mac cannot do that in its own conversation"


def belongs_to_the_host(arguments):
    return (
        any(option in arguments for option in HOST_OPTIONS)
        or arguments[:1] in ([verb] for verb in WINDOW_VERBS)
        or local_seat.health() is not None
    )


def status(arguments, directory):
    is_open = conversation_state.observe(directory) is ConversationPhase.OPEN
    report = {
        "open": is_open,
        "live": False,
        "seat": SEAT if is_open else None,
        "last_heard": utterances.last_heard(directory),
    }
    print(json.dumps(report))


def wait_until_the_seat_attaches():
    deadline = time.monotonic() + ATTACH_WAIT_SECONDS
    while not mac_seat_client.attached():
        if time.monotonic() > deadline:
            raise TimeoutError(SEAT_DID_NOT_ATTACH)
        time.sleep(POLL_SECONDS)


def end_conversation(directory):
    mac_seat_client.hush()
    listener_session.stop_listening()
    mac_seat_client.close_browser()
    for record in PRIVATE_RECORDS:
        (directory / record).unlink(missing_ok=True)
    conversation_addressee.forget(directory)


def open_conversation(arguments, directory):
    if arguments.character:
        print(VOICE_ONLY, file=sys.stderr)
    try:
        listener_session.begin_listening(
            directory,
            ListenerPurpose.CONVERSATION,
            {"human": MICROPHONE},
            language=arguments.language,
            barge_in=True,
        )
        wait_until_the_seat_attaches()
    except BaseException:
        end_conversation(directory)
        raise
    status(arguments, directory)


def close_conversation(arguments, directory):
    end_conversation(directory)
    print(json.dumps({"open": False}))


def speak(arguments, directory):
    pane = os.environ.get(voice_turns.PANE_ENVIRONMENT_VARIABLE)
    if not conversation_addressee.addresses(directory, pane):
        raise RuntimeError(ROOM_HELD_ELSEWHERE)
    holder = conversation_addressee.current(directory)
    voice = arguments.voice or mac_speech.voice_of(holder.servant if holder else None)
    recording = mac_speech.synthesized(arguments.text, arguments.emotion, voice)
    if mac_seat_client.attached():
        mac_seat_client.play(mac_speech.samples_of(recording))
    else:
        mac_speech.play_without_a_seat(recording)


def ask(arguments, directory):
    with utterances.exclusive_consumer(directory):
        speak(arguments, directory)
        voice_turns.print_next_utterance(directory, arguments.wait)


def refuse_closed(arguments, directory):
    raise utterances.ConversationClosed(utterances.CLOSED_MESSAGE)


def refuse_here(arguments, directory):
    raise RuntimeError(NOT_HERE)


ACTIONS = {
    ConversationAction.BRING_UP: open_conversation,
    ConversationAction.KEEP_OPEN: status,
    ConversationAction.TEAR_DOWN: close_conversation,
    ConversationAction.ASK: ask,
    ConversationAction.HEAR: voice_turns.hear,
    ConversationAction.FOLLOW: voice_turns.follow,
    ConversationAction.SAY: speak,
    ConversationAction.REPORT: status,
    ConversationAction.REFUSE_CLOSED: refuse_closed,
}


def carry_out_here(arguments):
    parsed = parse_arguments(arguments)
    directory = listener_runtime.runtime_directory()
    decision = conversation_state.decide(
        conversation_state.observe(directory), ConversationCommand(parsed.action)
    )
    ACTIONS.get(decision, refuse_here)(parsed, directory)
    return 0


def carry_out(arguments):
    if belongs_to_the_host(arguments):
        return remote_talk.carry_out(
            remote_talk.with_the_agent_that_receives_live_tasks(arguments)
        )
    return carry_out_here(arguments)


def main():
    try:
        sys.exit(carry_out(sys.argv[1:]))
    except (
        utterances.ConversationClosed,
        subprocess.SubprocessError,
        RuntimeError,
        TimeoutError,
        ValueError,
        OSError,
    ) as error:
        print(error, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
