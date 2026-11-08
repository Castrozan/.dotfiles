import audio_ownership
import pulse_audio
from audio_effects import CHANNELS as CHANNELS
from audio_effects import LIP_SYNC_SINK as LIP_SYNC_SINK
from audio_effects import MEETING_SOURCE as MEETING_SOURCE
from audio_effects import MIX_SINK as MIX_SINK
from audio_effects import (
    attach_default_and_unmute,
    attach_source,
    build,
    rebuild,
    set_channel,
    tear_down,
    unmute_inputs,
)


def start(path, state):
    perform(path, state, audio_ownership.AudioCommand.START)


def stop(path, state):
    perform(path, state, audio_ownership.AudioCommand.STOP)


def open_meeting_inputs(path, state):
    perform(path, state, audio_ownership.AudioCommand.OPEN)


def connect_microphone(path, state, source_name):
    perform(path, state, audio_ownership.AudioCommand.ATTACH, source=source_name)


def refuse_not_running():
    raise ValueError("Avatar audio is not running with its owned graph")


def refuse_already_attached():
    raise ValueError("A human input is already attached; stop before changing it")


def perform(path, state, command, **arguments):
    phase = audio_ownership.observe(state, pulse_audio.items("modules"))
    action = audio_ownership.decide(phase, command)
    effects = {
        audio_ownership.AudioAction.REPORT: lambda: None,
        audio_ownership.AudioAction.BUILD: lambda: build(path, state),
        audio_ownership.AudioAction.REBUILD: lambda: rebuild(path, state),
        audio_ownership.AudioAction.TEAR_DOWN: lambda: tear_down(path, state),
        audio_ownership.AudioAction.ATTACH_DEFAULT_AND_UNMUTE: lambda: (
            attach_default_and_unmute(path, state)
        ),
        audio_ownership.AudioAction.UNMUTE: unmute_inputs,
        audio_ownership.AudioAction.ATTACH_SOURCE: lambda: attach_source(
            path, state, arguments["source"]
        ),
        audio_ownership.AudioAction.SET_CHANNEL: lambda: set_channel(
            arguments["channel"], command.value, arguments["value"]
        ),
        audio_ownership.AudioAction.REFUSE_NOT_RUNNING: refuse_not_running,
        audio_ownership.AudioAction.REFUSE_ALREADY_ATTACHED: refuse_already_attached,
    }
    effects[action]()
