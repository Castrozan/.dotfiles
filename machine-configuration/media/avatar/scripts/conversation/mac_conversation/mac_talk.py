import os
import subprocess
import sys

import conversation_addressee
import conversation_report
import conversation_state
import listener
import listener_runtime
import listener_session
import local_seat
import mac_seat_client
import mac_stage
import remote_agent
import remote_talk
import room_reach
import utterances
import voice_turns
from conversation_state import ConversationAction, ConversationCommand
from conversation_state import ConversationPhase
from listener_session import ListenerPurpose
from talk_arguments import parse_arguments

MICROPHONE = "the microphone of this Mac"
SEAT = "room"
ATTACH_WAIT_SECONDS = 25
HOST_OPTIONS = ("--live", "--seat")
PRIVATE_RECORDS = (
    "transcript.jsonl",
    listener.EMBEDDINGS_FILE,
    listener.HEARD_FILE,
    listener_session.SPOKEN_FILE,
)
ROOM_HELD_ELSEWHERE = "Another session holds the room; it speaks until the room turns"
SEAT_DID_NOT_ATTACH = (
    f"The conversation page did not attach; check that {local_seat.BROWSER} "
    "may use the microphone"
)
NOT_HERE = "This Mac cannot do that in its own conversation"


def belongs_to_the_host(arguments):
    return (
        any(option in arguments for option in HOST_OPTIONS)
        or local_seat.conversation_listening()
    )


def leave_a_seat_the_host_stopped_using():
    if local_seat.health() is None or local_seat.meeting_held():
        return
    if not local_seat.meeting_seat_kept_here():
        local_seat.leave()


def status(arguments, directory):
    is_open = conversation_state.observe(directory) is ConversationPhase.OPEN
    conversation_report.print_status(
        directory, is_open=is_open, live=False, seat=SEAT if is_open else None
    )


def wait_until_the_seat_attaches():
    local_seat.wait_until(
        mac_seat_client.attached, ATTACH_WAIT_SECONDS, SEAT_DID_NOT_ATTACH
    )


def end_conversation(directory):
    leave_a_seat_the_host_stopped_using()
    mac_seat_client.hush()
    listener_session.stop_listening()
    mac_seat_client.close_browser()
    mac_stage.strike()
    for record in PRIVATE_RECORDS:
        (directory / record).unlink(missing_ok=True)
    conversation_addressee.forget(directory)


def open_conversation(arguments, directory):
    leave_a_seat_the_host_stopped_using()
    try:
        mac_stage.set_up()
        mac_stage.show_character(arguments.character)
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
    conversation_report.print_closed()


def speak(arguments, directory):
    pane = os.environ.get(remote_agent.PANE_ENVIRONMENT_VARIABLE)
    if not conversation_addressee.addresses(directory, pane):
        raise RuntimeError(ROOM_HELD_ELSEWHERE)
    listener_session.mark_spoken(directory)
    with mac_stage.standing():
        mac_stage.speak(arguments.text, arguments.emotion, arguments.voice)


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
    ConversationAction.SHOW: lambda arguments, directory: mac_stage.show_window(),
    ConversationAction.HIDE: lambda arguments, directory: mac_stage.hide_window(),
    ConversationAction.REFUSE_CLOSED: refuse_closed,
}


def make_room_for_the_host(arguments):
    directory = listener_runtime.runtime_directory()
    opening = arguments[:1] == ["open"]
    if opening and conversation_state.observe(directory) is ConversationPhase.OPEN:
        end_conversation(directory)


def carry_out_here(arguments):
    parsed = parse_arguments(arguments)
    directory = listener_runtime.runtime_directory()
    decision = conversation_state.decide(
        conversation_state.observe(directory), ConversationCommand(parsed.action)
    )
    ACTIONS.get(decision, refuse_here)(parsed, directory)
    return 0


def carry_out(arguments):
    forwarded = room_reach.forwarded_from_this_machine(arguments)
    if forwarded is not None:
        return forwarded
    if belongs_to_the_host(arguments):
        make_room_for_the_host(arguments)
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
