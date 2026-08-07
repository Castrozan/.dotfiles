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


def test_pattern_matching_ignores_case():
    profiles = (profile_named("work", ["GitLab.Example.com"]),)

    assert (
        match_git_remote_pattern(profiles, "git@gitlab.example.com:t/s.git").name
        == "work"
    )


def test_an_unrelated_remote_url_matches_nothing():
    profiles = (profile_named("work", ["gitlab.example.com"]),)

    assert (
        match_git_remote_pattern(profiles, "git@github.com:someone/thing.git") is None
    )


def test_an_absent_remote_url_matches_nothing():
    profiles = (profile_named("work", ["gitlab.example.com"]),)

    assert match_git_remote_pattern(profiles, None) is None


def test_reading_the_remote_url_of_a_directory_without_git_returns_nothing(monkeypatch):
    def failing_lookup(*_arguments, **_keyword_arguments):
        raise OSError("git is not installed")

    monkeypatch.setattr(subprocess, "run", failing_lookup)

    assert read_origin_remote_url(Path("/does/not/matter")) is None


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


def test_reading_the_remote_url_returns_nothing_when_git_reports_failure(monkeypatch):
    def failing_lookup(*_arguments, **_keyword_arguments):
        return subprocess.CompletedProcess(
            args=(), returncode=128, stdout="", stderr="fatal"
        )

    monkeypatch.setattr(subprocess, "run", failing_lookup)

    assert read_origin_remote_url(Path("/repo")) is None
