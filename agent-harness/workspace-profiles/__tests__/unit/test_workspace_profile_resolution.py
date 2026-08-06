from pathlib import Path

from workspace_profile_routing.profile_resolution import resolve_workspace_profile
from workspace_profile_routing.routing_table_loading import WorkspaceProfileRoute


def work_profile(tmp_path):
    return WorkspaceProfileRoute(
        name="work",
        directory_prefixes=(str(tmp_path / "repo"),),
        git_remote_patterns=("gitlab.example.com",),
    )


def never_reads_a_remote(_working_directory):
    raise AssertionError(
        "the git remote lookup must not run once a directory prefix matched"
    )


def test_a_directory_prefix_resolves_without_consulting_git(tmp_path):
    working_directory = tmp_path / "repo" / "service"
    working_directory.mkdir(parents=True)

    resolution = resolve_workspace_profile(
        profiles=(work_profile(tmp_path),),
        working_directory=working_directory,
        read_remote_url=never_reads_a_remote,
    )

    assert resolution.profile_name == "work"
    assert "matched under" in resolution.explanation


def test_a_git_remote_resolves_a_checkout_outside_every_declared_prefix(tmp_path):
    resolution = resolve_workspace_profile(
        profiles=(work_profile(tmp_path),),
        working_directory=tmp_path / "worktrees" / "service",
        read_remote_url=lambda _directory: "git@gitlab.example.com:team/service.git",
    )

    assert resolution.profile_name == "work"
    assert "git remote" in resolution.explanation


def test_an_unmatched_directory_resolves_to_no_profile_and_stays_silent(tmp_path):
    resolution = resolve_workspace_profile(
        profiles=(work_profile(tmp_path),),
        working_directory=tmp_path / "elsewhere",
        read_remote_url=lambda _directory: "git@github.com:someone/thing.git",
    )

    assert resolution.profile_name is None
    assert resolution.explanation is None


def test_the_git_lookup_is_skipped_when_no_profile_declares_a_remote_pattern(tmp_path):
    profiles = (
        WorkspaceProfileRoute(
            name="work",
            directory_prefixes=(str(tmp_path / "repo"),),
            git_remote_patterns=(),
        ),
    )

    resolution = resolve_workspace_profile(
        profiles=profiles,
        working_directory=tmp_path / "elsewhere",
        read_remote_url=never_reads_a_remote,
    )

    assert resolution.profile_name is None


def test_a_requested_profile_overrides_the_directory_it_launches_from(tmp_path):
    other_profile = WorkspaceProfileRoute(
        name="personal", directory_prefixes=(), git_remote_patterns=()
    )
    working_directory = tmp_path / "repo" / "service"
    working_directory.mkdir(parents=True)

    resolution = resolve_workspace_profile(
        profiles=(work_profile(tmp_path), other_profile),
        working_directory=working_directory,
        requested_profile_name="personal",
        read_remote_url=never_reads_a_remote,
    )

    assert resolution.profile_name == "personal"
    assert "forced by AGENT_WORKSPACE_PROFILE" in resolution.explanation


def test_requesting_none_disables_routing_without_explaining_itself(tmp_path):
    working_directory = tmp_path / "repo" / "service"
    working_directory.mkdir(parents=True)

    resolution = resolve_workspace_profile(
        profiles=(work_profile(tmp_path),),
        working_directory=working_directory,
        requested_profile_name="none",
        read_remote_url=never_reads_a_remote,
    )

    assert resolution.profile_name is None
    assert resolution.explanation is None


def test_requesting_an_undeclared_profile_falls_back_and_says_so(tmp_path):
    resolution = resolve_workspace_profile(
        profiles=(work_profile(tmp_path),),
        working_directory=Path(tmp_path),
        requested_profile_name="typo",
        read_remote_url=never_reads_a_remote,
    )

    assert resolution.profile_name is None
    assert "typo" in resolution.explanation
