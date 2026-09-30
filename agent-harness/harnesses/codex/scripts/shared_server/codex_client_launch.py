import os
import sys

from codex_client_configuration import command_line_configuration
from codex_client_control import register_client
from codex_client_arguments import NONINTERACTIVE_COMMANDS, parse_launch_arguments


def main():
    try:
        binary = os.environ["CODEX_LAUNCHER_BINARY"]
        if parse_launch_arguments(sys.argv[1:]).command in NONINTERACTIVE_COMMANDS:
            os.execv(binary, [binary, *sys.argv[1:]])
        endpoint = register_client(
            dict(os.environ), command_line_configuration(sys.argv[1:])
        )
        if endpoint is None:
            os.execv(binary, [binary, "--no-daemon", *sys.argv[1:]])
        os.execv(binary, [binary, "--remote", "unix://" + endpoint, *sys.argv[1:]])
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Codex shared server: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
