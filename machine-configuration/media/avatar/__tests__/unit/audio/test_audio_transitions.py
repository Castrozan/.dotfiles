import itertools

import audio_ownership
from audio_ownership import AudioAction, AudioCommand, AudioPhase


EXPECTED_TRANSITIONS = {
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

CORE_MODULE = {
    "index": 1,
    "name": "module-null-sink",
    "argument": "sink_name=AvatarMix",
}
MICROPHONE_MODULE = {
    "index": 2,
    "name": "module-loopback",
    "argument": "source=synthetic-human.monitor sink=AvatarHuman",
}

EXPECTED_PHASES = {
    (False, False, False, "matching"): AudioPhase.ABSENT,
    (False, False, False, "vanished"): AudioPhase.ABSENT,
    (False, False, False, "absent"): AudioPhase.ABSENT,
    (False, False, True, "matching"): AudioPhase.ABSENT,
    (False, False, True, "vanished"): AudioPhase.ABSENT,
    (False, False, True, "absent"): AudioPhase.ABSENT,
    (False, True, False, "matching"): AudioPhase.ABSENT,
    (False, True, False, "vanished"): AudioPhase.ABSENT,
    (False, True, False, "absent"): AudioPhase.ABSENT,
    (False, True, True, "matching"): AudioPhase.ABSENT,
    (False, True, True, "vanished"): AudioPhase.ABSENT,
    (False, True, True, "absent"): AudioPhase.ABSENT,
    (True, False, False, "matching"): AudioPhase.ORPHANED,
    (True, False, False, "vanished"): AudioPhase.ORPHANED,
    (True, False, False, "absent"): AudioPhase.ORPHANED,
    (True, False, True, "matching"): AudioPhase.ORPHANED,
    (True, False, True, "vanished"): AudioPhase.ORPHANED,
    (True, False, True, "absent"): AudioPhase.ORPHANED,
    (True, True, False, "matching"): AudioPhase.ORPHANED,
    (True, True, False, "vanished"): AudioPhase.ORPHANED,
    (True, True, False, "absent"): AudioPhase.ORPHANED,
    (True, True, True, "matching"): AudioPhase.RUNNING_ATTACHED,
    (True, True, True, "vanished"): AudioPhase.RUNNING_DETACHED,
    (True, True, True, "absent"): AudioPhase.RUNNING_DETACHED,
}


def test_transition_table_fills_every_phase_and_command_as_pinned():
    assert set(audio_ownership.TRANSITIONS) == set(AudioPhase)
    for phase in AudioPhase:
        assert set(audio_ownership.TRANSITIONS[phase]) == set(AudioCommand)
    assert audio_ownership.TRANSITIONS == EXPECTED_TRANSITIONS
    decisions = {
        (phase, command): audio_ownership.decide(phase, command)
        for phase, command in itertools.product(AudioPhase, AudioCommand)
    }
    assert decisions == {
        (phase, command): action
        for phase, cells in EXPECTED_TRANSITIONS.items()
        for command, action in cells.items()
    }


def test_observe_derives_phase_for_every_combination_of_world_facts():
    observed = {}
    for recorded, ready, core_matches, microphone in itertools.product(
        (False, True), (False, True), (False, True), ("matching", "vanished", "absent")
    ):
        present = [CORE_MODULE] if core_matches else []
        if microphone == "matching":
            present.append(MICROPHONE_MODULE)
        state = {"modules": [CORE_MODULE] if recorded else [], "ready": ready}
        if microphone != "absent":
            state["microphone"] = MICROPHONE_MODULE
        observed[(recorded, ready, core_matches, microphone)] = audio_ownership.observe(
            state, present
        )
    assert observed == EXPECTED_PHASES
