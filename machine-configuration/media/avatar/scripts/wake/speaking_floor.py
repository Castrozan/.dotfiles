import dataclasses

import conversation_addressee
from conversation_addressee import Addressee


@dataclasses.dataclass(frozen=True)
class FloorBoundaries:
    sessions: object
    listening: object


def first_claim(pane, sessions, holder):
    claimer = next((session for session in sessions if session.pane == pane), None)
    if claimer is None:
        return None
    return Addressee(pane, claimer.servant, holder.heard_through if holder else 0)


def claim(directory, pane, boundaries):
    with conversation_addressee.exclusive(directory):
        holder = conversation_addressee.current(directory)
        if holder and holder.pane == pane:
            return holder
        if not boundaries.listening():
            return None
        sessions = boundaries.sessions()
        if holder and any(session.pane == holder.pane for session in sessions):
            return holder
        claimer = first_claim(pane, sessions, holder)
        if claimer:
            conversation_addressee.write(directory, claimer)
        return claimer


def may_speak(holder, pane):
    return holder is None or holder.pane == pane
