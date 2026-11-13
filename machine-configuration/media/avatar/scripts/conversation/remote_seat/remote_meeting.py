import contextlib
import shlex
import subprocess
import sys

import local_seat
import meeting_camera

REMOTE_SEAT = "remote"
MEETING_PAGE_QUERY = "?meeting"
START_TIMEOUT_SECONDS = 180
STOP_TIMEOUT_SECONDS = 120
CALL_DEVICES_READY = (
    "Avatar ready. In the call, select the camera OBS Virtual Camera, "
    "the microphone BlackHole 2ch and the speaker BlackHole 16ch"
)
USAGE = "Usage: avatar-start | avatar-stop | avatar-listen ARGS"


def chise_command(program, arguments):
    return ["ssh", local_seat.AVATAR_HOST, shlex.join([program, *arguments])]


def start():
    started = subprocess.run(
        chise_command("avatar-start", ["--seat", REMOTE_SEAT]),
        timeout=START_TIMEOUT_SECONDS,
    )
    if started.returncode:
        raise RuntimeError(
            f"avatar-start failed on {local_seat.AVATAR_HOST} with exit code {started.returncode}"
        )
    try:
        local_seat.take(MEETING_PAGE_QUERY)
        meeting_camera.start()
    except BaseException:
        with contextlib.suppress(OSError, subprocess.SubprocessError):
            stop()
        raise
    print(CALL_DEVICES_READY)
    return 0


def stop():
    meeting_camera.stop()
    local_seat.leave()
    return subprocess.run(
        chise_command("avatar-stop", []), timeout=STOP_TIMEOUT_SECONDS
    ).returncode


def gives_a_seat(arguments):
    return any(
        argument == "--seat" or argument.startswith("--seat=") for argument in arguments
    )


def listen_arguments(arguments):
    if arguments[:1] != ["start"] or gives_a_seat(arguments):
        return arguments
    if not local_seat.attached():
        return arguments
    return [*arguments, "--seat", REMOTE_SEAT]


def listen(arguments):
    return subprocess.run(
        chise_command("avatar-listen", listen_arguments(arguments)),
        timeout=local_seat.LONGEST_SEAT_SECONDS,
    ).returncode


MEETING_STEPS = {"start": start, "stop": stop}


def carry_out(verb, arguments):
    if verb == "listen":
        return listen(arguments)
    if verb in MEETING_STEPS and not arguments:
        return MEETING_STEPS[verb]()
    raise RuntimeError(USAGE)


def main():
    verb, *arguments = sys.argv[1:] or [""]
    try:
        sys.exit(carry_out(verb, arguments))
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
