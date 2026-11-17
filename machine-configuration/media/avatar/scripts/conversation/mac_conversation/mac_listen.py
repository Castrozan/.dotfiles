import argparse
import subprocess
import sys

import listen_cli
import listener_runtime
import mac_meeting


def start(arguments):
    parser = argparse.ArgumentParser(prog="avatar-listen start")
    parser.add_argument("--language")
    mac_meeting.listen_to_the_call(
        listener_runtime.runtime_directory(), parser.parse_args(arguments).language
    )


def main():
    if sys.argv[1:2] != ["start"]:
        listen_cli.main()
        return
    try:
        start(sys.argv[2:])
    except (RuntimeError, TimeoutError, OSError, subprocess.SubprocessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
