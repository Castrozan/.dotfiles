import itertools
import json
import os
import re
import shlex
import subprocess
import sys

import local_seat
import local_window

PRESENT_WITHIN_SECONDS = 300
IDLE_TIME = re.compile(r'"HIDIdleTime" = (\d+)')
NANOSECONDS = 1_000_000_000
REMOTE_SEAT = "remote"
OPEN_TIMEOUT_SECONDS = 120
PANE_ENVIRONMENT_VARIABLE = "HERDR_PANE_ID"
HOST_ENVIRONMENT_VARIABLE = "AVATAR_AGENT_HOST"
LIVE_NEEDS_A_PANE = (
    "avatar-talk open --live must run from an agent's herdr pane: the live voice hands "
    "the room's tasks to that agent"
)
WINDOW_STEPS = {"show": local_window.show, "hide": local_window.hide}


def seconds_since_input():
    report = subprocess.run(
        ["/usr/sbin/ioreg", "-c", "IOHIDSystem"],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    ).stdout
    idle = IDLE_TIME.search(report)
    return int(idle.group(1)) / NANOSECONDS if idle else float("inf")


def user_is_here():
    return seconds_since_input() < PRESENT_WITHIN_SECONDS


def forward_command(arguments):
    return ["ssh", local_seat.AVATAR_HOST, "avatar-talk", shlex.join(arguments)]


def forward(arguments):
    return subprocess.run(
        forward_command(arguments), timeout=local_seat.LONGEST_SEAT_SECONDS
    ).returncode


def reported_seat(status_output):
    lines = status_output.strip().splitlines()
    try:
        return json.loads(lines[-1]).get("seat") if lines else None
    except ValueError:
        return None


def with_the_remote_seat(arguments):
    if asks_for_the_remote_seat(arguments):
        return arguments
    return [*arguments, "--seat", REMOTE_SEAT]


def open_here(arguments):
    opened = subprocess.run(
        forward_command(with_the_remote_seat(arguments)),
        stdout=subprocess.PIPE,
        text=True,
        timeout=OPEN_TIMEOUT_SECONDS,
    )
    sys.stdout.write(opened.stdout)
    sys.stdout.flush()
    if opened.returncode:
        return opened.returncode
    if reported_seat(opened.stdout) == REMOTE_SEAT and not seat_held_here():
        local_seat.take()
    return 0


def seat_held_here():
    return local_seat.attached() or local_seat.meeting_seat_kept_here()


def close_everywhere(arguments):
    returncode = forward(arguments)
    if not (local_seat.meeting_held() or local_seat.meeting_seat_kept_here()):
        local_seat.leave()
    return returncode


def move_window_here(arguments):
    returncode = forward(arguments)
    if returncode == 0:
        WINDOW_STEPS[arguments[0]]()
    return returncode


def moves_the_window_of_a_seat_held_here(arguments):
    return (
        len(arguments) == 1 and arguments[0] in WINDOW_STEPS and local_seat.attached()
    )


def opens_a_seated_conversation(arguments):
    return arguments[:1] == ["open"] and "--seat" not in arguments


def asks_for_the_remote_seat(arguments):
    return ("--seat", REMOTE_SEAT) in itertools.pairwise(arguments)


def opens_here(arguments):
    if arguments[:1] != ["open"]:
        return False
    if asks_for_the_remote_seat(arguments):
        return True
    return opens_a_seated_conversation(arguments) and user_is_here()


def with_the_agent_that_receives_live_tasks(arguments):
    if arguments[:1] != ["open"] or "--live" not in arguments:
        return arguments
    host = os.environ.get(HOST_ENVIRONMENT_VARIABLE)
    pane = os.environ.get(PANE_ENVIRONMENT_VARIABLE)
    if not host or not pane:
        raise RuntimeError(LIVE_NEEDS_A_PANE)
    return [*arguments, "--agent", f"{host}:{pane}"]


def carry_out(arguments):
    if opens_here(arguments):
        return open_here(arguments)
    if arguments[:1] == ["close"]:
        return close_everywhere(arguments)
    if moves_the_window_of_a_seat_held_here(arguments):
        return move_window_here(arguments)
    return forward(arguments)


def main():
    try:
        sys.exit(carry_out(with_the_agent_that_receives_live_tasks(sys.argv[1:])))
    except (RuntimeError, TimeoutError, subprocess.SubprocessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
