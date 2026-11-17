import subprocess
import sys

import listener_runtime
import mac_meeting

USAGE = "Usage: avatar-start | avatar-stop | avatar-controls"
MEETING_STEPS = {
    "start": mac_meeting.start,
    "stop": mac_meeting.stop,
    "controls": mac_meeting.controls,
}


def carry_out(verb, arguments):
    if verb not in MEETING_STEPS or arguments:
        raise RuntimeError(USAGE)
    MEETING_STEPS[verb](listener_runtime.runtime_directory())
    return 0


def main():
    verb, *arguments = sys.argv[1:] or [""]
    try:
        sys.exit(carry_out(verb, arguments))
    except (RuntimeError, TimeoutError, OSError, subprocess.SubprocessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
