import argparse
import json

import audio
import audio_state
import pulse_audio


def describe(state):
    modules = pulse_audio.items("modules")
    return {
        "running": bool(state.get("ready"))
        and all(
            audio_state.matches_module(entry, modules) for entry in state["modules"]
        ),
        "microphone": state.get("microphone"),
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
    for action in ("start", "stop", "status"):
        commands.add_parser(action)
    attach = commands.add_parser("attach")
    attach.add_argument("source")
    for operation in ("mute", "volume"):
        command = commands.add_parser(operation)
        command.add_argument("channel", choices=audio.CHANNELS)
        command.add_argument("value", type=int)
    return parser.parse_args()


def attach(arguments, path, state):
    audio.require_owned_graph(state)
    audio.connect_microphone(path, state, arguments.source)


def mute(arguments, path, state):
    if arguments.value not in (0, 1):
        raise ValueError("Mute must be 0 or 1")
    audio.set_channel(state, arguments.channel, "mute", str(arguments.value))


def volume(arguments, path, state):
    if not 0 <= arguments.value <= 100:
        raise ValueError("Volume must be between 0 and 100")
    audio.set_channel(state, arguments.channel, "volume", f"{arguments.value}%")


def run(arguments, path, state):
    operations = {
        "start": lambda: audio.start(path, state),
        "stop": lambda: audio.stop(path, state),
        "attach": lambda: attach(arguments, path, state),
        "mute": lambda: mute(arguments, path, state),
        "volume": lambda: volume(arguments, path, state),
        "status": lambda: None,
    }
    operations[arguments.action]()
    print(json.dumps(describe(state)))


def main():
    arguments = parse_arguments()
    with audio_state.exclusive_state() as path:
        run(arguments, path, audio_state.read_state(path))


if __name__ == "__main__":
    main()
