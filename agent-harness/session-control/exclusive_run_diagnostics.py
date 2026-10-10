import re
import sys
import time
from datetime import datetime
from pathlib import Path

from exclusive_run_owner import OWNER_FIELDS, single_line


def bounded_number(value, maximum_digits):
    if re.fullmatch(r"[0-9]{1," + str(maximum_digits) + r"}", value or ""):
        return int(value)
    return 0


def read_metadata(lock_path):
    try:
        with Path(lock_path).open() as metadata:
            content = metadata.read(8192)
    except (OSError, UnicodeError):
        return {}
    return {
        name: single_line(value)
        for line in content.splitlines()
        if "=" in line
        for name, value in [line.split("=", 1)]
    }


def formatted_started_at(started_epoch):
    try:
        return datetime.fromtimestamp(started_epoch).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError, OverflowError):
        return "unknown"


def contention_diagnostics(lock_name, lock_path):
    metadata = read_metadata(lock_path)
    process_identifier = bounded_number(metadata.get("pid"), 10) or "unknown"
    started_epoch = bounded_number(metadata.get("started_epoch"), 10)
    typical_duration = bounded_number(metadata.get("typical_duration_seconds"), 9)
    elapsed = max(0, int(time.time()) - started_epoch)
    remaining = max(0, typical_duration - elapsed)
    fields = {
        "script": lock_name,
        "in_progress_pid": process_identifier,
        "started_at": f"{formatted_started_at(started_epoch)} ({elapsed}s ago)",
        "typical_duration": f"{typical_duration}s",
        "estimated_remaining": f"~{remaining}s",
        **{name: metadata.get(name) for name in OWNER_FIELDS},
        "in_progress_log": metadata.get("log_path"),
    }
    print("LOCKED_BY_CONCURRENT_RUN", file=sys.stderr)
    for name, value in fields.items():
        if value:
            print(f"{name + ':':<22}{value}", file=sys.stderr)
    if not metadata.get("owner_type"):
        print(f"{'owner_type:':<22}unknown", file=sys.stderr)
    print(
        "\nThis request was rejected; nothing was queued.\n"
        f"Run '{lock_name}' again intentionally after the owning run and its children finish.\n"
        "The lock can remain held after the metadata PID exits.\n"
        f"Recommended wait: at least {remaining + 30}s.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    contention_diagnostics(*sys.argv[1:3])
