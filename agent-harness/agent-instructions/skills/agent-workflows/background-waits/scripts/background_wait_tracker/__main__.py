from __future__ import annotations

import argparse
import json
import sys

from .silent_background_commands import NOTIFIED_LATE, silent_command_record
from .silent_command_ledger import (
    default_ledger_path,
    dismiss_record,
    load_records_by_id,
    record_silent_commands,
)
from .transcript_background_runs import background_command_runs_in_transcript
from .transcript_discovery import (
    default_transcripts_root,
    recent_transcripts_launching_background_commands,
)
from .wait_guard_verdict import wait_guard_denial_rule_names, wait_shape_name

SECONDS_PER_MINUTE = 60
LISTED_COMMAND_CHARACTERS = 160


def build_argument_parser():
    parser = argparse.ArgumentParser(
        prog="background-wait-tracker",
        description=(
            "Record backgrounded Bash and Monitor commands that stayed silent for "
            "a long time, read from Claude Code transcripts, and show which of "
            "them the background wait guard still allows."
        ),
    )
    parser.add_argument("--ledger", default=str(default_ledger_path()))
    subcommands = parser.add_subparsers(dest="subcommand", required=True)

    scan = subcommands.add_parser(
        "scan", help="read transcripts and record silent background commands"
    )
    scan.add_argument("--transcripts-root", default=default_transcripts_root())
    scan.add_argument(
        "--transcript",
        action="append",
        default=[],
        help="scan only this transcript; repeat for several",
    )
    scan.add_argument("--since-days", type=float, default=7)
    scan.add_argument("--minimum-silent-minutes", type=float, default=30)

    listing = subcommands.add_parser(
        "list",
        help=(
            "recorded commands that never notified, which the guard still allows "
            "and nobody dismissed"
        ),
    )
    listing.add_argument(
        "--all",
        action="store_true",
        help="include late-notifying, denied and dismissed records",
    )
    listing.add_argument("--json", action="store_true")

    show = subcommands.add_parser("show", help="print one record in full")
    show.add_argument("record_id")

    dismiss = subcommands.add_parser(
        "dismiss", help="mark a record as a good shape that was merely slow"
    )
    dismiss.add_argument("record_id")
    dismiss.add_argument("--reason", required=True)
    return parser


def command_scan(arguments):
    transcript_paths = (
        arguments.transcript
        or recent_transcripts_launching_background_commands(
            arguments.transcripts_root, arguments.since_days
        )
    )
    minimum_silent_seconds = arguments.minimum_silent_minutes * SECONDS_PER_MINUTE
    silent_command_records = [
        record
        for transcript_path in transcript_paths
        for run in background_command_runs_in_transcript(transcript_path)
        if (
            record := silent_command_record(
                run, transcript_path, minimum_silent_seconds
            )
        )
    ]
    newly_recorded_ids = record_silent_commands(
        arguments.ledger, silent_command_records
    )
    print(
        f"scanned {len(transcript_paths)} transcripts; "
        f"{len(silent_command_records)} silent commands, "
        f"{len(newly_recorded_ids)} new, in {arguments.ledger}"
    )
    return 0


def record_with_guard_verdict(record):
    denial_rule_names = wait_guard_denial_rule_names(
        record["tool_name"], record["command"]
    )
    return {
        **record,
        "denied_now_by": denial_rule_names,
        "wait_shape": wait_shape_name(record["tool_name"], record["command"]),
    }


def record_still_needs_a_decision(judged_record):
    return (
        judged_record["outcome"] != NOTIFIED_LATE
        and not judged_record["denied_now_by"]
        and not judged_record["dismissed_reason"]
    )


def command_list(arguments):
    judged_records = [
        record_with_guard_verdict(record)
        for record in load_records_by_id(arguments.ledger).values()
    ]
    listed_records = [
        judged_record
        for judged_record in judged_records
        if arguments.all or record_still_needs_a_decision(judged_record)
    ]
    if arguments.json:
        print(json.dumps(listed_records, ensure_ascii=False, indent=1))
        return 0
    for judged_record in listed_records:
        print_listed_record(judged_record)
    return 0


def print_listed_record(judged_record):
    verdict = (
        "denied:" + ",".join(judged_record["denied_now_by"])
        if judged_record["denied_now_by"]
        else f"allowed:{judged_record['wait_shape']}"
    )
    one_line_command = " ".join(judged_record["command"].split())
    print(
        "\t".join(
            (
                judged_record["id"],
                f"{judged_record['silent_minutes']}m",
                judged_record["outcome"],
                judged_record["tool_name"],
                "dismissed" if judged_record["dismissed_reason"] else verdict,
                one_line_command[:LISTED_COMMAND_CHARACTERS],
            )
        )
    )


def command_show(arguments):
    record = load_records_by_id(arguments.ledger).get(arguments.record_id)
    if record is None:
        print(
            f"background-wait-tracker: no record {arguments.record_id}", file=sys.stderr
        )
        return 1
    print(json.dumps(record_with_guard_verdict(record), ensure_ascii=False, indent=1))
    return 0


def command_dismiss(arguments):
    try:
        dismiss_record(arguments.ledger, arguments.record_id, arguments.reason)
    except KeyError:
        print(
            f"background-wait-tracker: no record {arguments.record_id}", file=sys.stderr
        )
        return 1
    return 0


COMMAND_HANDLERS_BY_SUBCOMMAND = {
    "scan": command_scan,
    "list": command_list,
    "show": command_show,
    "dismiss": command_dismiss,
}


def main():
    arguments = build_argument_parser().parse_args()
    return COMMAND_HANDLERS_BY_SUBCOMMAND[arguments.subcommand](arguments)


if __name__ == "__main__":
    sys.exit(main())
