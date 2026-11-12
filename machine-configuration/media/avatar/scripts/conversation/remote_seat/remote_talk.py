import json
import re
import shlex
import subprocess
import sys

import local_seat

PRESENT_WITHIN_SECONDS = 300
IDLE_TIME = re.compile(r'"HIDIdleTime" = (\d+)')
NANOSECONDS = 1_000_000_000
REMOTE_SEAT = "remote"


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
    return subprocess.run(forward_command(arguments)).returncode


def reported_seat(status_output):
    lines = status_output.strip().splitlines()
    try:
        return json.loads(lines[-1]).get("seat") if lines else None
    except ValueError:
        return None


def open_here(arguments):
    opened = subprocess.run(
        forward_command([*arguments, "--seat", REMOTE_SEAT]),
        stdout=subprocess.PIPE,
        text=True,
    )
    sys.stdout.write(opened.stdout)
    sys.stdout.flush()
    if opened.returncode:
        return opened.returncode
    if reported_seat(opened.stdout) == REMOTE_SEAT and not local_seat.attached():
        local_seat.take()
    return 0


def close_everywhere(arguments):
    returncode = forward(arguments)
    local_seat.leave()
    return returncode


def opens_a_seated_conversation(arguments):
    return (
        arguments[:1] == ["open"]
        and "--live" not in arguments
        and "--seat" not in arguments
    )


def main():
    arguments = sys.argv[1:]
    try:
        if opens_a_seated_conversation(arguments) and user_is_here():
            sys.exit(open_here(arguments))
        if arguments[:1] == ["close"]:
            sys.exit(close_everywhere(arguments))
        sys.exit(forward(arguments))
    except (RuntimeError, TimeoutError, subprocess.SubprocessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
