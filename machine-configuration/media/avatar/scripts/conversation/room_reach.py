import os
import shlex
import socket
import subprocess
import sys

ROOM_VARIABLE = "AVATAR_ROOM"
HOST_VARIABLE = "AVATAR_AGENT_HOST"
PANE_VARIABLE = "HERDR_PANE_ID"
LONGEST_SEAT_SECONDS = 12 * 60 * 60
REACH_ROOM = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]


def this_host(environment):
    return environment.get(HOST_VARIABLE) or socket.gethostname().partition(".")[0]


def command_in_the_room(arguments, pane):
    identity = f"{PANE_VARIABLE}={shlex.quote(pane)} " if pane else ""
    return f"{identity}avatar-talk {shlex.join(arguments)}"


def forwarded_to_the_room(arguments, environment, this_host, run):
    room = environment.get(ROOM_VARIABLE)
    if not room or room == this_host:
        return None
    command = command_in_the_room(arguments, environment.get(PANE_VARIABLE))
    return run(
        [*REACH_ROOM, room, command], check=False, timeout=LONGEST_SEAT_SECONDS
    ).returncode


def forwarded_from_this_machine(arguments):
    try:
        return forwarded_to_the_room(
            arguments, os.environ, this_host(os.environ), subprocess.run
        )
    except (OSError, subprocess.SubprocessError) as error:
        print(error, file=sys.stderr)
        return 1
