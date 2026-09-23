from collections import defaultdict
from dataclasses import dataclass
from pathlib import PurePosixPath

DIRECTORY_ENTRY_LIMIT = 15


@dataclass(frozen=True)
class DirectoryEntryViolation:
    directory: str
    count: int
    ceiling: int

    def describe(self) -> str:
        return (
            f"{self.directory} has {self.count} immediate files/folders combined "
            f"(limit {self.ceiling}). Group related responsibilities into modules."
        )


def directory_entry_counts(repository_paths: list[str]) -> dict[str, int]:
    children = defaultdict(set)
    for repository_path in repository_paths:
        parts = PurePosixPath(repository_path).parts
        for index, entry in enumerate(parts):
            directory = "/".join(parts[:index]) or "."
            children[directory].add(entry)
    return {directory: len(entries) for directory, entries in children.items()}


def directory_entry_violations(counts, ceilings, directories=None):
    return [
        DirectoryEntryViolation(
            directory, count, ceilings.get(directory, DIRECTORY_ENTRY_LIMIT)
        )
        for directory, count in sorted(counts.items())
        if directory != "."
        and (directories is None or directory in directories)
        and count > ceilings.get(directory, DIRECTORY_ENTRY_LIMIT)
    ]
