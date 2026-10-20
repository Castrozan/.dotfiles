import argparse
import os
import re
import stat
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

SECONDS_PER_HOUR = 3600
APPLE_MANAGED_TOP_LEVEL_PREFIX = "com.apple."
APPLE_MANAGED_TOP_LEVEL_NAMES = frozenset(
    {".AddressBookLocks", ".LINKS", "TemporaryItems"}
)
PER_USER_TEMPORARY_DIRECTORY_PATTERN = re.compile(
    r"/(private/)?var/folders/[^/]+/[^/]+/T/?"
)
OWNER_READ_WRITE_AND_TRAVERSE = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR


@dataclass(frozen=True)
class CleanupPolicy:
    temporary_directory: Path
    stale_before_timestamp: float
    protected_top_level_names: frozenset[str]


@dataclass
class CleanupResult:
    removed_entry_count: int = 0
    failed_entry_count: int = 0
    first_failure: str | None = None


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


def is_protected_top_level_name(
    name: str, protected_top_level_names: frozenset[str]
) -> bool:
    return (
        name in protected_top_level_names
        or name in APPLE_MANAGED_TOP_LEVEL_NAMES
        or name.startswith(APPLE_MANAGED_TOP_LEVEL_PREFIX)
    )


def is_stale(entry_status: os.stat_result, stale_before_timestamp: float) -> bool:
    newest_timestamp = max(
        entry_status.st_atime, entry_status.st_mtime, entry_status.st_ctime
    )
    return newest_timestamp < stale_before_timestamp


def grant_owner_read_write_and_traverse(directory_path: str) -> None:
    directory_mode = stat.S_IMODE(os.lstat(directory_path).st_mode)
    os.chmod(
        directory_path,
        directory_mode | OWNER_READ_WRITE_AND_TRAVERSE,
        follow_symlinks=False,
    )


def retry_after_granting_directory_access[Outcome](
    operation: Callable[[str], Outcome], path: str, directory_to_grant: str
) -> Outcome:
    try:
        return operation(path)
    except PermissionError:
        grant_owner_read_write_and_traverse(directory_to_grant)
        return operation(path)


class StaleEntryRemover:
    def __init__(self, policy: CleanupPolicy) -> None:
        self.policy = policy
        self.root_device = os.lstat(policy.temporary_directory).st_dev
        self.result = CleanupResult()

    def remove_stale_top_level_entries(self) -> CleanupResult:
        for top_level_name in os.listdir(self.policy.temporary_directory):
            if is_protected_top_level_name(
                top_level_name, self.policy.protected_top_level_names
            ):
                continue
            self.remove_when_stale(
                os.path.join(self.policy.temporary_directory, top_level_name)
            )
        return self.result

    def remove_when_stale(self, entry_path: str) -> bool:
        try:
            entry_status = os.lstat(entry_path)
        except FileNotFoundError:
            return True
        if entry_status.st_dev != self.root_device:
            return False
        if stat.S_ISDIR(entry_status.st_mode):
            return self.remove_directory_when_stale_and_emptied(
                entry_path, entry_status
            )
        if not (
            stat.S_ISREG(entry_status.st_mode) or stat.S_ISLNK(entry_status.st_mode)
        ):
            return False
        if not is_stale(entry_status, self.policy.stale_before_timestamp):
            return False
        return self.remove(os.unlink, entry_path)

    def remove_directory_when_stale_and_emptied(
        self, directory_path: str, directory_status: os.stat_result
    ) -> bool:
        try:
            child_names = retry_after_granting_directory_access(
                os.listdir, directory_path, directory_path
            )
        except FileNotFoundError:
            return True
        except OSError as error:
            self.record_failure(directory_path, error)
            return False
        remaining_child_count = 0
        for child_name in child_names:
            if not self.remove_when_stale(os.path.join(directory_path, child_name)):
                remaining_child_count += 1
        if remaining_child_count or not is_stale(
            directory_status, self.policy.stale_before_timestamp
        ):
            return False
        return self.remove(os.rmdir, directory_path)

    def remove(self, remove_operation: Callable[[str], None], entry_path: str) -> bool:
        try:
            retry_after_granting_directory_access(
                remove_operation, entry_path, os.path.dirname(entry_path)
            )
        except FileNotFoundError:
            return True
        except OSError as error:
            self.record_failure(entry_path, error)
            return False
        self.result.removed_entry_count += 1
        return True

    def record_failure(self, entry_path: str, error: OSError) -> None:
        self.result.failed_entry_count += 1
        if self.result.first_failure is None:
            self.result.first_failure = f"{entry_path}: {error.strerror}"


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
