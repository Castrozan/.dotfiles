from __future__ import annotations

import argparse
import re
import sys

from .file_line_wait import first_line_matching
from .process_exit_wait import every_process_exits_within

TIMED_OUT_EXIT_CODE = 124
FOLLOW_FAILED_EXIT_CODE = 2


def build_argument_parser():
    parser = argparse.ArgumentParser(
        prog="wait-for-event",
        description=(
            "Block until a file gains a matching line or processes exit, woken by "
            "the kernel's own file and process events instead of a sleep loop."
        ),
        epilog="Exit codes: 0 event seen, 2 cannot follow, 124 timed out.",
    )
    timeout_option = argparse.ArgumentParser(add_help=False)
    timeout_option.add_argument("--timeout-seconds", type=float, default=None)
    events = parser.add_subparsers(dest="event", required=True)
    file_event = events.add_parser(
        "file",
        parents=[timeout_option],
        help="print the first line matching --match, existing or appended",
    )
    file_event.add_argument("path")
    file_event.add_argument("--match", required=True, help="Python regular expression")
    process_event = events.add_parser(
        "process",
        parents=[timeout_option],
        help="return once every listed process has exited",
    )
    process_event.add_argument("process_ids", nargs="+", type=int, metavar="pid")
    return parser


def wait_for_file_line(arguments):
    try:
        matching_line = first_line_matching(
            arguments.path, re.compile(arguments.match), arguments.timeout_seconds
        )
    except EOFError:
        print(f"cannot follow {arguments.path}", file=sys.stderr)
        return FOLLOW_FAILED_EXIT_CODE
    if matching_line is None:
        print(f"timed out waiting for {arguments.match!r}", file=sys.stderr)
        return TIMED_OUT_EXIT_CODE
    print(matching_line, flush=True)
    return 0


def wait_for_process_exits(arguments):
    if not every_process_exits_within(arguments.process_ids, arguments.timeout_seconds):
        print("timed out with a process still running", file=sys.stderr)
        return TIMED_OUT_EXIT_CODE
    print("exited " + " ".join(map(str, arguments.process_ids)), flush=True)
    return 0


EVENT_WAITERS_BY_NAME = {
    "file": wait_for_file_line,
    "process": wait_for_process_exits,
}


def main(argv=None):
    arguments = build_argument_parser().parse_args(argv)
    return EVENT_WAITERS_BY_NAME[arguments.event](arguments)


if __name__ == "__main__":
    sys.exit(main())
