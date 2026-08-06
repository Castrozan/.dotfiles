import subprocess
from pathlib import Path

from .routing_table_loading import WorkspaceProfileRoute

GIT_REMOTE_LOOKUP_TIMEOUT_SECONDS = 5


def read_origin_remote_url(working_directory: Path) -> str | None:
    try:
        completed_lookup = subprocess.run(
            ["git", "-C", str(working_directory), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=False,
            timeout=GIT_REMOTE_LOOKUP_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed_lookup.returncode != 0:
        return None
    return completed_lookup.stdout.strip() or None


def match_git_remote_pattern(
    profiles: tuple[WorkspaceProfileRoute, ...],
    remote_url: str | None,
) -> WorkspaceProfileRoute | None:
    if not remote_url:
        return None
    lowercased_remote_url = remote_url.lower()
    for profile in profiles:
        for declared_pattern in profile.git_remote_patterns:
            if declared_pattern.lower() in lowercased_remote_url:
                return profile
    return None
