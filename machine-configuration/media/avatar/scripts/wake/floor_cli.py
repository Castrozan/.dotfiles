import os
import sys

import listener_runtime
import speaking_floor
from servant_panes import live_sessions

PANE_ENVIRONMENT_VARIABLE = "HERDR_PANE_ID"


def main():
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


if __name__ == "__main__":
    main()
