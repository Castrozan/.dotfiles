from workspace_profile_routing.directory_prefix_matching import (
    match_longest_directory_prefix,
)
from workspace_profile_routing.routing_table_loading import WorkspaceProfileRoute


def profile_named(name, directory_prefixes):
    return WorkspaceProfileRoute(
        name=name,
        directory_prefixes=tuple(directory_prefixes),
        git_remote_patterns=(),
    )


def test_a_directory_inside_a_declared_prefix_matches(tmp_path):
    working_directory = tmp_path / "repo" / "some-service"
    working_directory.mkdir(parents=True)
    profiles = (profile_named("work", [str(tmp_path / "repo")]),)

    match = match_longest_directory_prefix(profiles, working_directory)

    assert match.profile.name == "work"


def test_the_declared_prefix_itself_matches(tmp_path):
    profiles = (profile_named("work", [str(tmp_path)]),)

    assert match_longest_directory_prefix(profiles, tmp_path).profile.name == "work"


def test_a_directory_outside_every_prefix_matches_nothing(tmp_path):
    outside_directory = tmp_path / "elsewhere"
    outside_directory.mkdir()
    profiles = (profile_named("work", [str(tmp_path / "repo")]),)

    assert match_longest_directory_prefix(profiles, outside_directory) is None


def test_a_sibling_directory_sharing_a_name_prefix_does_not_match(tmp_path):
    sibling_directory = tmp_path / "repository"
    sibling_directory.mkdir()
    profiles = (profile_named("work", [str(tmp_path / "repo")]),)

    assert match_longest_directory_prefix(profiles, sibling_directory) is None


def test_the_longest_prefix_wins_over_a_broader_one(tmp_path):
    working_directory = tmp_path / "repo" / "client" / "service"
    working_directory.mkdir(parents=True)
    profiles = (
        profile_named("work", [str(tmp_path / "repo")]),
        profile_named("client", [str(tmp_path / "repo" / "client")]),
    )

    assert (
        match_longest_directory_prefix(profiles, working_directory).profile.name
        == "client"
    )


def test_a_prefix_declared_with_a_home_shorthand_expands(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    working_directory = tmp_path / "repo"
    working_directory.mkdir()
    profiles = (profile_named("work", ["~/repo"]),)

    assert (
        match_longest_directory_prefix(profiles, working_directory).profile.name
        == "work"
    )


def test_a_working_directory_that_no_longer_exists_still_matches(tmp_path):
    profiles = (profile_named("work", [str(tmp_path / "repo")]),)

    match = match_longest_directory_prefix(
        profiles, tmp_path / "repo" / "deleted-clone"
    )

    assert match.profile.name == "work"
