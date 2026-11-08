import argparse
import json

import audio
import audio_ownership
import audio_state
import pulse_audio


RUNNING_PHASES = (
    audio_ownership.AudioPhase.RUNNING_DETACHED,
    audio_ownership.AudioPhase.RUNNING_ATTACHED,
)


def describe(state):
    modules = pulse_audio.items("modules")
    phase = audio_ownership.observe(state, modules)
    microphone = state.get("microphone")
    return {
        "running": phase in RUNNING_PHASES,
        "phase": phase.value,
        "microphone": microphone["source"] if microphone else None,
        "meeting_source": audio.MEETING_SOURCE,
        "channels": {
            channel: {key: sink.get(key) for key in ("name", "mute", "volume")}
            for channel, name in audio.CHANNELS.items()
            for sink in pulse_audio.items("sinks")
            if sink["name"] == name
        },
    }


def parse_arguments():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="action", required=True)
    for action in ("start", "stop", "status", "open"):
        commands.add_parser(action)
    attach = commands.add_parser("attach")
    attach.add_argument("source")
    for operation in ("mute", "volume"):
        command = commands.add_parser(operation)
        command.add_argument("channel", choices=audio.CHANNELS)
        command.add_argument("value", type=int)
    return parser.parse_args()


def validate_mute(value):
    if value not in (0, 1):
        raise ValueError("Mute must be 0 or 1")
    return str(value)


def validate_volume(value):
    if not 0 <= value <= 100:
        raise ValueError("Volume must be between 0 and 100")
    return f"{value}%"


def command_arguments(arguments):
    if arguments.action == audio_ownership.AudioCommand.ATTACH:
        return {"source": arguments.source}
    if arguments.action == audio_ownership.AudioCommand.MUTE:
        return {"channel": arguments.channel, "value": validate_mute(arguments.value)}
    if arguments.action == audio_ownership.AudioCommand.VOLUME:
        return {"channel": arguments.channel, "value": validate_volume(arguments.value)}
    return {}


def run(arguments, path, state):
    audio.perform(
        path,
        state,
        audio_ownership.AudioCommand(arguments.action),
        **command_arguments(arguments),
    )
    print(json.dumps(describe(state)))


def main():
    arguments = parse_arguments()
    with audio_state.exclusive_state() as path:
        state = audio_state.read_state(path)
        audio_ownership.release_vanished_microphone(
            path, state, pulse_audio.items("modules")
        )
        run(arguments, path, state)


if __name__ == "__main__":
    main()
