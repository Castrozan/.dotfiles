import os
import socket
import subprocess
import sys

import remote_agent

ROOM_VARIABLE = "AVATAR_ROOM"


def this_host(environment):
    return (
        environment.get(remote_agent.HOST_ENVIRONMENT_VARIABLE)
        or socket.gethostname().partition(".")[0]
    )


def command_in_the_room(arguments, pane):
    identity = (
        ["env", f"{remote_agent.PANE_ENVIRONMENT_VARIABLE}={pane}"] if pane else []
    )
    return [*identity, "avatar-talk", *arguments]


def forwarded_to_the_room(arguments, environment, this_host, run):
    room = environment.get(ROOM_VARIABLE)
    if not room or room == this_host:
        return None
    command = command_in_the_room(
        arguments, environment.get(remote_agent.PANE_ENVIRONMENT_VARIABLE)
    )
    return run(
        remote_agent.on_host(room, command),
        check=False,
        timeout=remote_agent.LONGEST_SEAT_SECONDS,
    ).returncode


def forwarded_from_this_machine(arguments):
    try:
        return forwarded_to_the_room(
            arguments, os.environ, this_host(os.environ), subprocess.run
        )
    except (OSError, subprocess.SubprocessError) as error:
        print(error, file=sys.stderr)
        return 1
