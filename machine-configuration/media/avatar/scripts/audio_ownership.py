import enum

import audio_state


class GraphPhase(enum.Enum):
    ABSENT = "absent"
    RUNNING = "running"
    ORPHANED = "orphaned"


def graph_phase(state, modules):
    if not state["modules"]:
        return GraphPhase.ABSENT
    if state.get("ready") and all(
        audio_state.matches_module(entry, modules) for entry in state["modules"]
    ):
        return GraphPhase.RUNNING
    return GraphPhase.ORPHANED


def microphone_is_live(state, modules):
    microphone = state.get("microphone")
    return microphone is not None and audio_state.matches_module(microphone, modules)


def release_vanished_microphone(path, state, modules):
    if state.get("microphone") and not microphone_is_live(state, modules):
        state["microphone"] = None
        audio_state.write_state(path, state)
