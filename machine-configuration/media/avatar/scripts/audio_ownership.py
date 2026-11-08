import enum

import audio_state


class AudioPhase(enum.StrEnum):
    ABSENT = "absent"
    RUNNING_DETACHED = "running-detached"
    RUNNING_ATTACHED = "running-attached"
    ORPHANED = "orphaned"


class AudioCommand(enum.StrEnum):
    START = "start"
    STOP = "stop"
    OPEN = "open"
    ATTACH = "attach"
    MUTE = "mute"
    VOLUME = "volume"
    STATUS = "status"


class AudioAction(enum.StrEnum):
    REPORT = "report"
    BUILD = "build"
    REBUILD = "rebuild"
    TEAR_DOWN = "tear-down"
    ATTACH_DEFAULT_AND_UNMUTE = "attach-default-and-unmute"
    UNMUTE = "unmute"
    ATTACH_SOURCE = "attach-source"
    SET_CHANNEL = "set-channel"
    REFUSE_NOT_RUNNING = "refuse-not-running"
    REFUSE_ALREADY_ATTACHED = "refuse-already-attached"


TRANSITIONS = {
    AudioPhase.ABSENT: {
        AudioCommand.START: AudioAction.BUILD,
        AudioCommand.STOP: AudioAction.TEAR_DOWN,
        AudioCommand.OPEN: AudioAction.REFUSE_NOT_RUNNING,
        AudioCommand.ATTACH: AudioAction.REFUSE_NOT_RUNNING,
        AudioCommand.MUTE: AudioAction.REFUSE_NOT_RUNNING,
        AudioCommand.VOLUME: AudioAction.REFUSE_NOT_RUNNING,
        AudioCommand.STATUS: AudioAction.REPORT,
    },
    AudioPhase.RUNNING_DETACHED: {
        AudioCommand.START: AudioAction.REPORT,
        AudioCommand.STOP: AudioAction.TEAR_DOWN,
        AudioCommand.OPEN: AudioAction.ATTACH_DEFAULT_AND_UNMUTE,
        AudioCommand.ATTACH: AudioAction.ATTACH_SOURCE,
        AudioCommand.MUTE: AudioAction.SET_CHANNEL,
        AudioCommand.VOLUME: AudioAction.SET_CHANNEL,
        AudioCommand.STATUS: AudioAction.REPORT,
    },
    AudioPhase.RUNNING_ATTACHED: {
        AudioCommand.START: AudioAction.REPORT,
        AudioCommand.STOP: AudioAction.TEAR_DOWN,
        AudioCommand.OPEN: AudioAction.UNMUTE,
        AudioCommand.ATTACH: AudioAction.REFUSE_ALREADY_ATTACHED,
        AudioCommand.MUTE: AudioAction.SET_CHANNEL,
        AudioCommand.VOLUME: AudioAction.SET_CHANNEL,
        AudioCommand.STATUS: AudioAction.REPORT,
    },
    AudioPhase.ORPHANED: {
        AudioCommand.START: AudioAction.REBUILD,
        AudioCommand.STOP: AudioAction.TEAR_DOWN,
        AudioCommand.OPEN: AudioAction.REFUSE_NOT_RUNNING,
        AudioCommand.ATTACH: AudioAction.REFUSE_NOT_RUNNING,
        AudioCommand.MUTE: AudioAction.REFUSE_NOT_RUNNING,
        AudioCommand.VOLUME: AudioAction.REFUSE_NOT_RUNNING,
        AudioCommand.STATUS: AudioAction.REPORT,
    },
}


def microphone_is_live(state, modules):
    microphone = state.get("microphone")
    return microphone is not None and audio_state.matches_module(microphone, modules)


def core_graph_matches(state, modules):
    return bool(state.get("ready")) and all(
        audio_state.matches_module(entry, modules) for entry in state["modules"]
    )


def observe(state, modules):
    if not state["modules"]:
        return AudioPhase.ABSENT
    if not core_graph_matches(state, modules):
        return AudioPhase.ORPHANED
    if microphone_is_live(state, modules):
        return AudioPhase.RUNNING_ATTACHED
    return AudioPhase.RUNNING_DETACHED


def decide(phase, command):
    return TRANSITIONS[phase][command]


def release_vanished_microphone(path, state, modules):
    if state.get("microphone") and not microphone_is_live(state, modules):
        state["microphone"] = None
        audio_state.write_state(path, state)
