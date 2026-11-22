import contextlib
import json
import os
import subprocess
import sys
import time
from types import SimpleNamespace

import conversation_addressee
import conversation_seat
import conversation_state
import listener_session
import remote_agent
import transcript_log
import turn_taking
import utterances
from conversation_state import ConversationPhase

FOLLOW_SLICE_SECONDS = 30
SPEECH_TIMEOUT_SECONDS = 310
VOICE_TAG = "[voice]"
ACKNOWLEDGEMENT = "speakAck"
SPEECH_MOMENTS = {
    "received": "speech_received",
    "synthesisStarted": "synthesis_started",
    "synthesized": "synthesized",
    "playing": "playing",
}


def this_pane():
    return os.environ.get(remote_agent.PANE_ENVIRONMENT_VARIABLE)


def acknowledgement(output):
    for line in output.splitlines():
        with contextlib.suppress(ValueError):
            response = json.loads(line)
            if isinstance(response, dict) and response.get("type") == ACKNOWLEDGEMENT:
                return response
    return {}


def speech_moments(response):
    timing = response.get("timing") or {}
    return {
        moment: timing[key] / 1000
        for key, moment in SPEECH_MOMENTS.items()
        if key in timing
    }


def spoken(command, invoked):
    completed = subprocess.run(
        command, stdout=subprocess.PIPE, text=True, timeout=SPEECH_TIMEOUT_SECONDS
    )
    response = acknowledgement(completed.stdout)
    transcript_log.report_speech(
        transcript_log.report_to_log,
        this_pane(),
        invoked=invoked,
        status=response.get("status"),
        source=response.get("source"),
        **speech_moments(response),
    )
    return completed


def withheld_speech(command, directory, reason, invoked):
    response = turn_taking.withhold(directory, reason)
    transcript_log.report_speech(
        transcript_log.report_to_log,
        this_pane(),
        invoked=invoked,
        status=response["status"],
        reason=reason,
    )
    return subprocess.CompletedProcess(command, 0, json.dumps(response) + "\n")


def spoken_in_turn(command, directory):
    invoked = time.time()
    reason = turn_taking.withheld_reason(directory)
    if reason:
        return withheld_speech(command, directory, reason, invoked)
    completed = spoken(command, invoked)
    status = acknowledgement(completed.stdout).get("status")
    turn_taking.remember_outcome(directory, status)
    return completed


def print_and_exit(completed):
    print(completed.stdout, end="", flush=True)
    sys.exit(completed.returncode)


def speech_command_on_seat(arguments, seat):
    voice = [arguments.voice] if arguments.voice else []
    return [
        "avatar-command",
        "speak",
        arguments.text,
        arguments.emotion,
        conversation_seat.SPEECH_OUTPUT_BY_SEAT[seat],
        *voice,
    ]


def speech_command(arguments, directory):
    return speech_command_on_seat(arguments, conversation_seat.current(directory))


def speak_on_seat(directory, text, seat):
    listener_session.mark_spoken(directory)
    subprocess.run(
        speech_command_on_seat(
            SimpleNamespace(text=text, emotion="neutral", voice=None), seat
        ),
        check=True,
        timeout=SPEECH_TIMEOUT_SECONDS,
    )


def say(arguments, directory):
    listener_session.mark_spoken(directory)
    print_and_exit(spoken(speech_command(arguments, directory), time.time()))


def reply(arguments, directory):
    listener_session.mark_spoken(directory)
    print_and_exit(spoken_in_turn(speech_command(arguments, directory), directory))


def print_next_utterance(
    directory, wait_seconds, still_addressed=utterances.always_addressed
):
    utterance = utterances.next_utterance(
        directory,
        wait_seconds,
        lambda: conversation_state.observe(directory) is ConversationPhase.OPEN,
        still_addressed,
    )
    if utterance:
        print(f"{VOICE_TAG} {utterance}", flush=True)


def hear(arguments, directory):
    with utterances.exclusive_consumer(directory):
        print_next_utterance(directory, arguments.wait)


def listen_after(completed, directory, wait_seconds):
    completed.check_returncode()
    if acknowledgement(completed.stdout).get("status") == turn_taking.WITHHELD:
        print(completed.stdout, end="", flush=True)
    print_next_utterance(directory, wait_seconds)


def ask(arguments, directory):
    with utterances.exclusive_consumer(directory):
        listener_session.mark_spoken(directory)
        completed = spoken_in_turn(speech_command(arguments, directory), directory)
        listen_after(completed, directory, arguments.wait)


def follow(arguments, directory):
    pane = this_pane()

    def still_addressed():
        return conversation_addressee.addresses(directory, pane)

    with utterances.exclusive_consumer(directory):
        while still_addressed():
            print_next_utterance(directory, FOLLOW_SLICE_SECONDS, still_addressed)
    successor = conversation_addressee.current(directory)
    name = successor.servant if successor else "another session"
    print(f"{VOICE_TAG} The room turned to {name}; this follow has ended.", flush=True)
