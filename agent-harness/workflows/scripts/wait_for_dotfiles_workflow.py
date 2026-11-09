import argparse
import sys

from archon_runs import WAIT_COMMAND_NAME, report_run


def wait_command(command_line_arguments: list[str]) -> str:
    parser = argparse.ArgumentParser(
        prog=WAIT_COMMAND_NAME,
        description=(
            "Block until an Archon workflow run ends and print its result, "
            "keeping a non-interactive caller's turn open while the run works."
        ),
    )
    parser.add_argument("run_identifier", help="the run ID the workflow printed")
    return report_run(parser.parse_args(command_line_arguments).run_identifier)


def main() -> int:
    print(wait_command(sys.argv[1:]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
