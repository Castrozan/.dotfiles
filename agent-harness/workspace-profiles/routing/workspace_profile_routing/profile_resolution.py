from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .directory_prefix_matching import match_longest_directory_prefix
from .git_remote_matching import match_git_remote_pattern, read_origin_remote_url
from .routing_table_loading import WorkspaceProfileRoute

ROUTING_DISABLED_PROFILE_NAME = "none"


@dataclass(frozen=True)
class WorkspaceProfileResolution:
    profile_name: str | None
    explanation: str | None


NO_WORKSPACE_PROFILE = WorkspaceProfileResolution(profile_name=None, explanation=None)


def resolve_requested_profile(
    profiles: tuple[WorkspaceProfileRoute, ...],
    requested_profile_name: str,
) -> WorkspaceProfileResolution:
    if requested_profile_name == ROUTING_DISABLED_PROFILE_NAME:
        return NO_WORKSPACE_PROFILE
    if requested_profile_name not in {profile.name for profile in profiles}:
        return WorkspaceProfileResolution(
            profile_name=None,
            explanation=(
                f"AGENT_WORKSPACE_PROFILE names {requested_profile_name!r}, "
                "which no profile declares; launching with the global configuration"
            ),
        )
    return WorkspaceProfileResolution(
        profile_name=requested_profile_name,
        explanation=f"workspace profile {requested_profile_name}, forced by AGENT_WORKSPACE_PROFILE",
    )


def resolve_profile_for_directory(
    profiles: tuple[WorkspaceProfileRoute, ...],
    working_directory: Path,
    read_remote_url: Callable[[Path], str | None],
) -> WorkspaceProfileResolution:
    directory_match = match_longest_directory_prefix(profiles, working_directory)
    if directory_match is not None:
        return WorkspaceProfileResolution(
            profile_name=directory_match.profile.name,
            explanation=(
                f"workspace profile {directory_match.profile.name}, "
                f"matched under {directory_match.directory_prefix}"
            ),
        )
    if not any(profile.git_remote_patterns for profile in profiles):
        return NO_WORKSPACE_PROFILE
    remote_match = match_git_remote_pattern(
        profiles, read_remote_url(working_directory)
    )
    if remote_match is None:
        return NO_WORKSPACE_PROFILE
    return WorkspaceProfileResolution(
        profile_name=remote_match.name,
        explanation=f"workspace profile {remote_match.name}, matched by git remote",
    )


def resolve_workspace_profile(
    profiles: tuple[WorkspaceProfileRoute, ...],
    working_directory: Path,
    requested_profile_name: str | None = None,
    read_remote_url: Callable[[Path], str | None] = read_origin_remote_url,
) -> WorkspaceProfileResolution:
    if requested_profile_name:
        return resolve_requested_profile(profiles, requested_profile_name)
    return resolve_profile_for_directory(profiles, working_directory, read_remote_url)
