import argparse
import os
import subprocess
import sys

import conversation_addressee
import listener_runtime
import remote_agent
import servant_character
import speaking_floor
from servant_panes import live_sessions

PANE_ENVIRONMENT_VARIABLE = "HERDR_PANE_ID"
NO_SERVANT_MESSAGE = (
    "The pane has no Servant name: only a session with one can hold the avatar's floor."
)


def refuse_the_floor(holder):
    print(
        f"{holder.servant} holds the avatar's floor: stay silent until the room "
        "names you.",
        file=sys.stderr,
    )
    sys.exit(1)


def servant_of_pane(pane, holder):
    if holder:
        return holder.servant
    session = next(
        (session for session in live_sessions() if session.pane == pane), None
    )
    return session.servant if session else None


def claim_for_this_pane():
    pane = os.environ.get(PANE_ENVIRONMENT_VARIABLE)
    if not pane:
        return
    holder = speaking_floor.claim(
        listener_runtime.runtime_directory(),
        pane,
        speaking_floor.FloorBoundaries(live_sessions, listener_runtime.listening),
    )
    if not speaking_floor.may_speak(holder, pane):
        refuse_the_floor(holder)
    servant = servant_of_pane(pane, holder)
    if servant:
        servant_character.show_for(servant)


def unreadable_session(error):
    print(f"The agent's session could not be read: {error}", file=sys.stderr)
    sys.exit(1)


def hand_to_agent(agent, heard_through):
    try:
        handed = speaking_floor.hand_to_remote_agent(
            listener_runtime.runtime_directory(), agent, heard_through
        )
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        unreadable_session(error)
    if not handed:
        print(NO_SERVANT_MESSAGE, file=sys.stderr)
        sys.exit(1)


def claim_for_speaker(speaker):
    try:
        servant = remote_agent.servant_at(speaker)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        unreadable_session(error)
    holder = conversation_addressee.current(listener_runtime.runtime_directory())
    if holder and (holder.host, holder.pane) != (speaker.host, speaker.pane):
        refuse_the_floor(holder)
    if servant:
        servant_character.show_for(servant)


def main():
    parser = argparse.ArgumentParser(prog="avatar-claim-floor")
    who = parser.add_mutually_exclusive_group()
    who.add_argument("--agent", type=remote_agent.parse)
    who.add_argument("--speaker", type=remote_agent.parse)
    parser.add_argument("--heard-through", type=int, default=0)
    arguments = parser.parse_args()
    if arguments.heard_through and not arguments.agent:
        parser.error("--heard-through needs --agent")
    if arguments.agent:
        hand_to_agent(arguments.agent, arguments.heard_through)
    elif arguments.speaker:
        claim_for_speaker(arguments.speaker)
    else:
        claim_for_this_pane()


if __name__ == "__main__":
    main()
