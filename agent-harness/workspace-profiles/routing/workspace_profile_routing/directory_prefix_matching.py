from collections.abc import Iterator
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


def _directory_prefix_matches(
    profiles: tuple[WorkspaceProfileRoute, ...],
    canonical_working_directory: Path,
) -> Iterator[DirectoryPrefixMatch]:
    for profile in profiles:
        for declared_prefix in profile.directory_prefixes:
            canonical_prefix = canonical_directory(Path(declared_prefix))
            if directory_is_within_prefix(
                canonical_working_directory, canonical_prefix
            ):
                yield DirectoryPrefixMatch(
                    profile=profile, directory_prefix=canonical_prefix
                )


def match_longest_directory_prefix(
    profiles: tuple[WorkspaceProfileRoute, ...],
    working_directory: Path,
) -> DirectoryPrefixMatch | None:
    canonical_working_directory = canonical_directory(working_directory)
    return max(
        _directory_prefix_matches(profiles, canonical_working_directory),
        key=lambda match: len(match.directory_prefix.parts),
        default=None,
    )
