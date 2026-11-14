import argparse
import dataclasses
import json
import re
import subprocess
import sys

import conversation_addressee
import conversation_seat
import conversation_state
import listener
import listener_runtime
import listener_session
import speaker_identity
import transcript_log
from conversation_seat import Seat
from conversation_state import ConversationAction, ConversationCommand
from listener_session import ListenerPurpose

MEETING_AUDIO = "@DEFAULT_MONITOR@"
AVATAR_OUTPUTS = re.compile(r"^(AvatarMicrophone$|Avatar\w*\.monitor$)")
FOLLOW_WAIT_SECONDS = 30


def existing_sources():
    output = subprocess.check_output(["pactl", "list", "short", "sources"], text=True)
    return {line.split("\t")[1] for line in output.splitlines()}


def default_microphone():
    return subprocess.check_output(["pactl", "get-default-source"], text=True).strip()


def selected_sources(microphone):
    microphone = microphone or default_microphone()
    if AVATAR_OUTPUTS.match(microphone):
        raise ValueError("The avatar's own output cannot be its microphone")
    if microphone not in existing_sources():
        raise ValueError(f"Source does not exist: {microphone}")
    return {"meeting": MEETING_AUDIO, "human": microphone}


def remote_seat_sources(microphone):
    if microphone:
        raise ValueError("A remote seat's microphone is the Mac's; drop --microphone")
    return {
        "meeting": conversation_seat.REMOTE_MEETING_SOURCE,
        "human": conversation_seat.MICROPHONE_BY_SEAT[Seat.REMOTE],
    }


def listening_for(seat, microphone):
    if seat is Seat.REMOTE:
        return remote_seat_sources(microphone), {"seat": seat}
    return selected_sources(microphone), {}


def start(arguments, directory):
    decision = conversation_state.decide(
        conversation_state.observe(directory), ConversationCommand.TRANSCRIBE_MEETING
    )
    if decision is ConversationAction.REFUSE_CONVERSATION:
        raise ValueError(
            "A conversation is open; run avatar-talk close before transcribing a meeting"
        )
    sources, seat_settings = listening_for(arguments.seat, arguments.microphone)
    listener_session.begin_listening(
        directory,
        ListenerPurpose.MEETING,
        sources,
        language=arguments.language,
        identify_speakers=True,
        **seat_settings,
    )
    print(json.dumps({"listening": True, "sources": sources}))


def stop(arguments, directory):
    listener_session.stop_listening()
    print(json.dumps({"listening": False}))


def status(arguments, directory):
    print(
        json.dumps(
            {
                "listening": listener_runtime.listening(),
                "purpose": listener_session.configured_purpose(directory),
                "sources": listener_session.configured_sources(directory),
                "last_sequence": transcript_log.last_sequence(
                    directory / "transcript.jsonl"
                ),
            }
        )
    )


def addressee(arguments, directory):
    holder = conversation_addressee.current(directory)
    print(json.dumps(dataclasses.asdict(holder) if holder else None))


def print_entries(entries):
    for entry in entries:
        print(json.dumps(entry, ensure_ascii=False), flush=True)


def read(arguments, directory):
    print_entries(
        transcript_log.wait_since(
            directory / "transcript.jsonl", arguments.since, arguments.wait
        )
    )


def follow(arguments, directory):
    path = directory / "transcript.jsonl"
    sequence = arguments.since
    pattern = re.compile(arguments.match, re.IGNORECASE) if arguments.match else None
    while True:
        entries = transcript_log.wait_since(path, sequence, FOLLOW_WAIT_SECONDS)
        if entries:
            sequence = entries[-1]["sequence"]
        print_entries(
            entry for entry in entries if not pattern or pattern.search(entry["text"])
        )


def enroll(arguments, directory):
    samples = speaker_identity.enroll(
        speaker_identity.VoiceProfiles(speaker_identity.voices_directory()),
        directory / listener.EMBEDDINGS_FILE,
        arguments.name,
        arguments.first,
        arguments.last,
    )
    print(json.dumps({"enrolled": arguments.name, "samples": samples}))


def voices(arguments, directory):
    names = speaker_identity.VoiceProfiles(speaker_identity.voices_directory()).names()
    print(json.dumps({"voices": names}))


def forget(arguments, directory):
    speaker_identity.VoiceProfiles(speaker_identity.voices_directory()).forget(
        arguments.name
    )
    print(json.dumps({"forgotten": arguments.name}))


def parse_arguments():
    parser = argparse.ArgumentParser(prog="avatar-listen")
    commands = parser.add_subparsers(dest="action", required=True)
    begin = commands.add_parser("start")
    begin.add_argument("--microphone")
    begin.add_argument("--language")
    begin.add_argument("--seat", choices=list(Seat), type=Seat, default=Seat.ROOM)
    commands.add_parser("stop")
    commands.add_parser("status")
    commands.add_parser("addressee")
    reading = commands.add_parser("read")
    reading.add_argument("--since", type=int, default=0)
    reading.add_argument("--wait", type=float, default=0)
    following = commands.add_parser("follow")
    following.add_argument("--since", type=int, default=0)
    following.add_argument("--match")
    enrolling = commands.add_parser("enroll")
    enrolling.add_argument("name")
    enrolling.add_argument("--first", type=int, required=True)
    enrolling.add_argument("--last", type=int, required=True)
    commands.add_parser("voices")
    forgetting = commands.add_parser("forget")
    forgetting.add_argument("name")
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    actions = {
        "start": start,
        "stop": stop,
        "status": status,
        "addressee": addressee,
        "read": read,
        "follow": follow,
        "enroll": enroll,
        "voices": voices,
        "forget": forget,
    }
    try:
        actions[arguments.action](arguments, listener_runtime.runtime_directory())
    except ValueError as error:
        print(error, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
