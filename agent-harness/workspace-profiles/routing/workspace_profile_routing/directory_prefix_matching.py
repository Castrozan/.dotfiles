from dataclasses import dataclass
from pathlib import Path

from .routing_table_loading import WorkspaceProfileRoute


@dataclass(frozen=True)
class DirectoryPrefixMatch:
    profile: WorkspaceProfileRoute
    directory_prefix: Path


def canonical_directory(directory: Path) -> Path:
    return Path(directory).expanduser().resolve()


def directory_is_within_prefix(directory: Path, directory_prefix: Path) -> bool:
    return directory == directory_prefix or directory_prefix in directory.parents


def match_longest_directory_prefix(
    profiles: tuple[WorkspaceProfileRoute, ...],
    working_directory: Path,
) -> DirectoryPrefixMatch | None:
    canonical_working_directory = canonical_directory(working_directory)
    longest_match: DirectoryPrefixMatch | None = None
    for profile in profiles:
        for declared_prefix in profile.directory_prefixes:
            canonical_prefix = canonical_directory(Path(declared_prefix))
            if not directory_is_within_prefix(
                canonical_working_directory, canonical_prefix
            ):
                continue
            if longest_match is not None and len(canonical_prefix.parts) <= len(
                longest_match.directory_prefix.parts
            ):
                continue
            longest_match = DirectoryPrefixMatch(
                profile=profile, directory_prefix=canonical_prefix
            )
    return longest_match
