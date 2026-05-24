#!/usr/bin/env python3
"""Command-line entry point for managing today's manager report. Multiple sessions can call this concurrently; section writes are flock-protected."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from daily_report_file_layout import (  # noqa: E402
    NEXT_HEADER,
    TODAY_HEADER,
    ensure_report_exists,
    report_path_for,
    today_iso_date,
)
from daily_report_section_editing import (  # noqa: E402
    append_bullet_to_section,
    remove_bullet_matching,
    set_blockers_value,
    with_exclusive_lock_read_write,
)


def command_path(args):
    print(report_path_for(args.date))


def command_init(args):
    report_file_path = report_path_for(args.date)
    ensure_report_exists(report_file_path)
    print(report_file_path)


def command_show(args):
    report_file_path = report_path_for(args.date)
    ensure_report_exists(report_file_path)
    sys.stdout.write(report_file_path.read_text(encoding="utf-8"))


def command_add_today(args):
    with_exclusive_lock_read_write(
        report_path_for(args.date),
        lambda lines: append_bullet_to_section(lines, TODAY_HEADER, args.text),
    )


def command_add_next(args):
    with_exclusive_lock_read_write(
        report_path_for(args.date),
        lambda lines: append_bullet_to_section(lines, NEXT_HEADER, args.text),
    )


def command_remove_today(args):
    with_exclusive_lock_read_write(
        report_path_for(args.date),
        lambda lines: remove_bullet_matching(lines, TODAY_HEADER, args.match),
    )


def command_remove_next(args):
    with_exclusive_lock_read_write(
        report_path_for(args.date),
        lambda lines: remove_bullet_matching(lines, NEXT_HEADER, args.match),
    )


def command_set_blockers(args):
    with_exclusive_lock_read_write(
        report_path_for(args.date),
        lambda lines: set_blockers_value(lines, args.text),
    )


def build_argument_parser():
    parser = argparse.ArgumentParser(
        description="Manage the daily manager report file. Multiple sessions can call this concurrently; writes are flock-protected."
    )
    parser.add_argument(
        "--date",
        default=today_iso_date(),
        help="ISO date (YYYY-MM-DD) for the report. Defaults to today.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("path", help="Print today's report file path.").set_defaults(
        func=command_path
    )
    subparsers.add_parser(
        "init", help="Create today's report file with the empty template if missing."
    ).set_defaults(func=command_init)
    subparsers.add_parser("show", help="Print today's report contents.").set_defaults(
        func=command_show
    )

    add_today_parser = subparsers.add_parser(
        "add-today", help="Append a bullet to the Today section."
    )
    add_today_parser.add_argument("text", help="Bullet text, e.g. 'CAFE-529: fixed X'.")
    add_today_parser.set_defaults(func=command_add_today)

    add_next_parser = subparsers.add_parser(
        "add-next", help="Append a bullet to the Next section."
    )
    add_next_parser.add_argument("text", help="Bullet text, e.g. 'CAFE-534: kick off'.")
    add_next_parser.set_defaults(func=command_add_next)

    remove_today_parser = subparsers.add_parser(
        "remove-today", help="Remove the first Today bullet containing the substring."
    )
    remove_today_parser.add_argument("match", help="Substring to match.")
    remove_today_parser.set_defaults(func=command_remove_today)

    remove_next_parser = subparsers.add_parser(
        "remove-next", help="Remove the first Next bullet containing the substring."
    )
    remove_next_parser.add_argument("match", help="Substring to match.")
    remove_next_parser.set_defaults(func=command_remove_next)

    set_blockers_parser = subparsers.add_parser(
        "set-blockers",
        help="Set the Blockers line value. Use 'None' to clear.",
    )
    set_blockers_parser.add_argument("text", help="Blockers value or 'None'.")
    set_blockers_parser.set_defaults(func=command_set_blockers)

    return parser


def main():
    parser = build_argument_parser()
    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
