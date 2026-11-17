import dataclasses
import os
import subprocess

import conversation_addressee
import conversation_effects
import conversation_seat
import conversation_state
import listener_session
import speaking_floor
from meetings import start
from conversation_seat import Seat
from listener_session import ListenerPurpose
from remote_agent import PANE_ENVIRONMENT_VARIABLE, AgentPane

LIVE_NEEDS_A_PANE = (
    "avatar-talk open --live must run from an agent's herdr pane: the live voice hands "
    "the room's tasks to that agent"
)
LIVE_HAS_NO_DISCORD_SEAT = (
    "The live voice has no Discord seat; open a conversation instead"
)
LIVE_NEEDS_A_SERVANT = (
    "The live voice could not give the floor to this pane: only a session with a Servant "
    "name can hold it and receive the room's tasks"
)


@dataclasses.dataclass(frozen=True)
class LiveStage:
    bring_up: object
    wait_until_seated: object
    close: object


def bring_up_the_room_stage(seat):
    start.bring_up(
        conversation_state.CONVERSATION_TARGET,
        (
            start.renderer_ready,
            lambda: conversation_effects.seat_microphone_ready(seat),
        ),
    )


def close_the_room_session(arguments, directory):
    conversation_effects.close_conversation(arguments, directory)


ROOM_STAGE = LiveStage(bring_up_the_room_stage, lambda: None, close_the_room_session)


def receiving_agent(arguments):
    return arguments.agent or AgentPane(None, os.environ.get(PANE_ENVIRONMENT_VARIABLE))


def give_the_floor(directory, agent):
    if agent.host is None:
        subprocess.run(
            ["avatar-claim-floor"],
            check=True,
            timeout=conversation_effects.COMMAND_TIMEOUT_SECONDS,
        )
        return
    speaking_floor.hand_to_remote_agent(directory, agent)


def holds_the_floor(directory, agent):
    holder = conversation_addressee.current(directory)
    return holder is not None and (holder.host, holder.pane) == (agent.host, agent.pane)


def open_live_conversation(arguments, directory, stage=ROOM_STAGE):
    agent = receiving_agent(arguments)
    if not agent.pane:
        raise RuntimeError(LIVE_NEEDS_A_PANE)
    seat = conversation_seat.requested(arguments)
    if seat is Seat.DISCORD:
        raise RuntimeError(LIVE_HAS_NO_DISCORD_SEAT)
    try:
        stage.bring_up(seat)
        conversation_seat.prepare(seat)
        conversation_effects.show_chosen_character(arguments)
        listener_session.begin_listening(
            directory,
            ListenerPurpose.LIVE,
            {"human": conversation_seat.MICROPHONE_BY_SEAT[seat]},
            seat=seat,
        )
        stage.wait_until_seated()
        give_the_floor(directory, agent)
        if not holds_the_floor(directory, agent):
            raise RuntimeError(LIVE_NEEDS_A_SERVANT)
    except BaseException:
        stage.close(arguments, directory)
        raise
    conversation_effects.status(arguments, directory)
