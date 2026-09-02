#!/usr/bin/env python3
from __future__ import annotations

import sys
from datetime import datetime, timezone

LOCAL_TIME_FORMAT = "%Y-%m-%d %H:%M:%S %Z (%A)"
USAGE = """usage: local-time [--iso] [STAMP ...]
STAMP is ISO 8601 with a zone, such as 2026-09-02T18:53:47Z or 2026-09-02T15:53:47-03:00, or epoch seconds.
No STAMP prints now. --iso prints ISO 8601 with the local offset, ready for an API parameter."""


def instant_from_stamp(stamp: str) -> datetime:
    if stamp.isdigit():
        return datetime.fromtimestamp(int(stamp), tz=timezone.utc)
    try:
        parsed = datetime.fromisoformat(stamp)
    except ValueError as error:
        raise ValueError(f"cannot parse {stamp!r}: {error}") from error
    if parsed.tzinfo is None:
        raise ValueError(f"{stamp!r} carries no zone; add Z or an offset like -03:00")
    return parsed


def local_time_line(instant: datetime) -> str:
    return instant.astimezone().strftime(LOCAL_TIME_FORMAT)


def local_iso_line(instant: datetime) -> str:
    return instant.astimezone().isoformat(timespec="seconds")


def main(arguments: list[str]) -> int:
    if arguments[:1] in (["-h"], ["--help"]):
        print(USAGE)
        return 0
    render_line = local_time_line
    if arguments[:1] == ["--iso"]:
        render_line = local_iso_line
        arguments = arguments[1:]
    try:
        instants = (
            [instant_from_stamp(stamp) for stamp in arguments]
            if arguments
            else [datetime.now(timezone.utc)]
        )
    except ValueError as error:
        print(f"local-time: {error}", file=sys.stderr)
        return 2
    for instant in instants:
        print(render_line(instant))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
