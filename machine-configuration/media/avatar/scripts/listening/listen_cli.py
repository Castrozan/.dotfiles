import argparse
import json
import re
import subprocess
import sys

import conversation_state
import listener
import listener_session
import speaker_identity
import transcript_log
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


def start(arguments, directory):
    decision = conversation_state.decide(
        conversation_state.observe(directory), ConversationCommand.TRANSCRIBE_MEETING
    )
    if decision is ConversationAction.REFUSE_CONVERSATION:
        raise ValueError(
            "A conversation is open; run avatar-talk close before transcribing a meeting"
        )
    sources = selected_sources(arguments.microphone)
    listener_session.begin_listening(
        directory,
        ListenerPurpose.MEETING,
        sources,
        language=arguments.language,
        identify_speakers=True,
    )
    print(json.dumps({"listening": True, "sources": sources}))


def stop(arguments, directory):
    listener_session.stop_listening()
    print(json.dumps({"listening": False}))


def status(arguments, directory):
    print(
        json.dumps(
            {
                "listening": listener_session.listening(),
                "purpose": listener_session.configured_purpose(directory),
                "sources": listener_session.configured_sources(directory),
                "last_sequence": transcript_log.last_sequence(
                    directory / "transcript.jsonl"
                ),
            }
        )
    )


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
    commands.add_parser("stop")
    commands.add_parser("status")
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
        "read": read,
        "follow": follow,
        "enroll": enroll,
        "voices": voices,
        "forget": forget,
    }
    try:
        actions[arguments.action](arguments, listener.runtime_directory())
    except ValueError as error:
        print(error, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
