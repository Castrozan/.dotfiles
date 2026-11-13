import argparse
import os
import subprocess
import sys

import listener_runtime
import remote_agent
import speaking_floor
from servant_panes import live_sessions

PANE_ENVIRONMENT_VARIABLE = "HERDR_PANE_ID"
NO_SERVANT_MESSAGE = (
    "The pane has no Servant name: only a session with one can hold the avatar's floor."
)


def claim_for_this_pane():
    pane = os.environ.get(PANE_ENVIRONMENT_VARIABLE)
    if not pane:
        return
    holder = speaking_floor.claim(
        listener_runtime.runtime_directory(),
        pane,
        speaking_floor.FloorBoundaries(live_sessions, listener_runtime.listening),
    )
    if speaking_floor.may_speak(holder, pane):
        return
    print(
        f"{holder.servant} holds the avatar's floor: stay silent until the room "
        "names you.",
        file=sys.stderr,
    )
    sys.exit(1)


def hand_to_agent(agent):
    try:
        handed = speaking_floor.hand_to_remote_agent(
            listener_runtime.runtime_directory(), agent
        )
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"The agent's session could not be read: {error}", file=sys.stderr)
        sys.exit(1)
    if not handed:
        print(NO_SERVANT_MESSAGE, file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(prog="avatar-claim-floor")
    parser.add_argument("--agent", type=remote_agent.parse)
    arguments = parser.parse_args()
    if arguments.agent:
        hand_to_agent(arguments.agent)
    else:
        claim_for_this_pane()


if __name__ == "__main__":
    main()
