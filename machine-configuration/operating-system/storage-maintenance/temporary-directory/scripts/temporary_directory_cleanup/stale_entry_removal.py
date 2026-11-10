import os
import stat
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from examined_entry import ExaminedEntry

APPLE_MANAGED_TOP_LEVEL_PREFIX = "com.apple."
APPLE_MANAGED_TOP_LEVEL_NAMES = frozenset(
    {".AddressBookLocks", ".LINKS", "TemporaryItems"}
)
OWNER_READ_WRITE_AND_TRAVERSE = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
UNDELETABLE_FILE_FLAGS = stat.SF_NOUNLINK | stat.SF_IMMUTABLE | stat.UF_IMMUTABLE


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


def is_removable_file_type(file_mode: int) -> bool:
    return stat.S_ISDIR(file_mode) or stat.S_ISREG(file_mode) or stat.S_ISLNK(file_mode)


def grant_owner_read_write_and_traverse(directory_path: str) -> None:
    directory_mode = stat.S_IMODE(os.lstat(directory_path).st_mode)
    os.chmod(directory_path, directory_mode | OWNER_READ_WRITE_AND_TRAVERSE)


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
        return self.remove_examined_entry(self.examine(entry_path))

    def examine(self, entry_path: str) -> ExaminedEntry:
        try:
            entry_status = retry_after_granting_directory_access(
                os.lstat, entry_path, os.path.dirname(entry_path)
            )
        except FileNotFoundError:
            return ExaminedEntry(entry_path, status=None, already_absent=True)
        except OSError as error:
            self.record_failure(entry_path, error)
            return ExaminedEntry(entry_path, status=None)
        return ExaminedEntry(entry_path, entry_status)

    def remove_examined_entry(self, examined_entry: ExaminedEntry) -> bool:
        entry_status = examined_entry.status
        if entry_status is None:
            return examined_entry.already_absent
        if not self.is_eligible_for_removal(entry_status):
            return False
        if stat.S_ISDIR(entry_status.st_mode):
            return self.remove_directory_when_stale_and_emptied(
                examined_entry.path, entry_status
            )
        if not is_stale(entry_status, self.policy.stale_before_timestamp):
            return False
        return self.remove(os.unlink, examined_entry.path)

    def is_eligible_for_removal(self, entry_status: os.stat_result) -> bool:
        entry_flags = getattr(entry_status, "st_flags", 0)
        return (
            entry_status.st_dev == self.root_device
            and not entry_flags & UNDELETABLE_FILE_FLAGS
            and is_removable_file_type(entry_status.st_mode)
        )

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
        children_removed = self.remove_stale_children(directory_path, child_names)
        directory_was_stale = is_stale(
            directory_status, self.policy.stale_before_timestamp
        )
        if not (children_removed and directory_was_stale):
            return False
        return self.remove(os.rmdir, directory_path)

    def remove_stale_children(
        self, directory_path: str, child_names: list[str]
    ) -> bool:
        examined_children = [
            self.examine(os.path.join(directory_path, child_name))
            for child_name in child_names
        ]
        if any(child.is_interprocess_endpoint for child in examined_children):
            self.remove_examined_entries(
                child for child in examined_children if child.is_directory
            )
            return False
        return self.remove_examined_entries(examined_children)

    def remove_examined_entries(
        self, examined_entries: Iterable[ExaminedEntry]
    ) -> bool:
        removal_outcomes = [
            self.remove_examined_entry(examined_entry)
            for examined_entry in examined_entries
        ]
        return all(removal_outcomes)

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
