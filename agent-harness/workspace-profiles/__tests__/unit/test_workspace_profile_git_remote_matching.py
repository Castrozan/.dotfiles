import subprocess
from pathlib import Path

from workspace_profile_routing.git_remote_matching import (
    match_git_remote_pattern,
    read_origin_remote_url,
)
from workspace_profile_routing.routing_table_loading import WorkspaceProfileRoute


def profile_named(name, git_remote_patterns):
    return WorkspaceProfileRoute(
        name=name,
        directory_prefixes=(),
        git_remote_patterns=tuple(git_remote_patterns),
    )


def test_a_remote_url_containing_the_declared_pattern_matches():
    profiles = (profile_named("work", ["gitlab.example.com"]),)

    match = match_git_remote_pattern(
        profiles, "git@gitlab.example.com:team/service.git"
    )

    assert match.name == "work"


def test_reading_the_remote_url_returns_the_trimmed_origin_url(monkeypatch):
    def successful_lookup(*_arguments, **_keyword_arguments):
        return subprocess.CompletedProcess(
            args=(),
            returncode=0,
            stdout="git@gitlab.example.com:team/service.git\n",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", successful_lookup)

    assert (
        read_origin_remote_url(Path("/repo"))
        == "git@gitlab.example.com:team/service.git"
    )
