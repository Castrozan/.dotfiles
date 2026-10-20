import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

from stale_entry_removal import CleanupPolicy, StaleEntryRemover

SECONDS_PER_HOUR = 3600
PER_USER_TEMPORARY_DIRECTORY_PATTERN = re.compile(
    r"/(private/)?var/folders/[^/]+/[^/]+/T/?"
)


def resolve_per_user_temporary_directory() -> Path:
    completed_process = subprocess.run(
        ["/usr/bin/getconf", "DARWIN_USER_TEMP_DIR"],
        capture_output=True,
        text=True,
        check=True,
    )
    temporary_directory = completed_process.stdout.strip()
    if not PER_USER_TEMPORARY_DIRECTORY_PATTERN.fullmatch(temporary_directory):
        raise ValueError(
            f"refusing to clean unexpected temporary directory: {temporary_directory!r}"
        )
    return Path(temporary_directory)


def parse_arguments(arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="temporary-directory-cleanup")
    parser.add_argument("--maximum-age-hours", type=int, required=True)
    parser.add_argument(
        "--protect", action="append", default=[], metavar="TOP_LEVEL_NAME"
    )
    return parser.parse_args(arguments)


def main(arguments: list[str]) -> int:
    parsed_arguments = parse_arguments(arguments)
    policy = CleanupPolicy(
        temporary_directory=resolve_per_user_temporary_directory(),
        stale_before_timestamp=time.time()
        - parsed_arguments.maximum_age_hours * SECONDS_PER_HOUR,
        protected_top_level_names=frozenset(parsed_arguments.protect),
    )
    started_at = time.monotonic()
    result = StaleEntryRemover(policy).remove_stale_top_level_entries()
    elapsed_seconds = time.monotonic() - started_at
    print(
        f"{time.strftime('%Y-%m-%dT%H:%M:%S')} removed {result.removed_entry_count} stale entries "
        f"from {policy.temporary_directory} in {elapsed_seconds:.1f}s; {result.failed_entry_count} failed",
        flush=True,
    )
    if result.first_failure is not None:
        print(f"first failure: {result.first_failure}", file=sys.stderr, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
