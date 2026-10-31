import argparse
import json

import audio
import pulse_audio


def describe(state):
    modules = pulse_audio.items("modules")
    return {
        "running": bool(state.get("ready"))
        and all(audio.matches_module(entry, modules) for entry in state["modules"]),
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


def run(arguments, path, state):
    if arguments.action == "start":
        audio.start(path, state)
    elif arguments.action == "stop":
        audio.stop(path, state)
    elif arguments.action == "attach":
        audio.require_owned_graph(state)
        audio.connect_microphone(path, state, arguments.source)
    elif arguments.action == "mute":
        if arguments.value not in (0, 1):
            raise ValueError("Mute must be 0 or 1")
        audio.set_channel(state, arguments.channel, "mute", str(arguments.value))
    elif arguments.action == "volume":
        if not 0 <= arguments.value <= 100:
            raise ValueError("Volume must be between 0 and 100")
        audio.set_channel(state, arguments.channel, "volume", f"{arguments.value}%")
    print(json.dumps(describe(state)))


def main():
    arguments = parse_arguments()
    with audio.exclusive_state() as path:
        run(arguments, path, audio.read_state(path))


if __name__ == "__main__":
    main()
