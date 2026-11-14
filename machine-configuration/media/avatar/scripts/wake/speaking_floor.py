import dataclasses

import conversation_addressee
import remote_agent
import room_holder
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


def holder_has_a_live_session(holder, sessions):
    return bool(holder) and any(session.pane == holder.pane for session in sessions)


def claim_among_live_sessions(directory, pane, holder, sessions):
    if holder_has_a_live_session(holder, sessions):
        return holder
    claimer = first_claim(pane, sessions, holder)
    if claimer:
        conversation_addressee.write(directory, claimer)
    return claimer


def claim(directory, pane, boundaries):
    with conversation_addressee.exclusive(directory):
        holder = conversation_addressee.current(directory)
        if holder and holder.pane == pane:
            return holder
        if not boundaries.listening():
            return None
        return claim_among_live_sessions(directory, pane, holder, boundaries.sessions())


def may_speak(holder, pane):
    return holder is None or holder.pane == pane


def hand_to_remote_agent(directory, agent, heard_through=0):
    servant = remote_agent.servant_at(agent)
    if servant:
        room_holder.give_the_room_to(
            directory, Addressee(agent.pane, servant, heard_through, agent.host)
        )
    return bool(servant)
