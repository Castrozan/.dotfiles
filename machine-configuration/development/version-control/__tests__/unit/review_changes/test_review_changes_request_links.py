import os
from unittest.mock import MagicMock, patch

import pytest

import request_links
from review_command_runner import ReviewTargetError


@pytest.mark.parametrize(
    ("raw_target", "expected_link"),
    [
        (
            "https://gitlab.services.example/team/tools.marketplace/-/merge_requests/388",
            request_links.RequestLink(
                request_links.ForgeRepository(
                    "gitlab.services.example", "team/tools.marketplace"
                ),
                "388",
            ),
        ),
        (
            "https://gitlab.example/group/subgroup/project/-/merge_requests/7/diffs",
            request_links.RequestLink(
                request_links.ForgeRepository(
                    "gitlab.example", "group/subgroup/project"
                ),
                "7",
            ),
        ),
        (
            " https://github.com/Castrozan/.dotfiles/pull/243 ",
            request_links.RequestLink(
                request_links.ForgeRepository("github.com", "Castrozan/.dotfiles"),
                "243",
            ),
        ),
    ],
)
def test_parses_merge_request_and_pull_request_links(raw_target, expected_link):
    assert request_links.parse_request_link(raw_target) == expected_link


@pytest.mark.parametrize("raw_target", ["388", "!388", "feature/branch", ""])
def test_numbers_and_branches_are_not_links(raw_target):
    assert request_links.parse_request_link(raw_target) is None


def test_finds_every_distinct_link_in_rendered_markdown_in_order():
    reply_text = (
        "Review [!388](https://gitlab.example/group/project/-/merge_requests/388),"
        " then <https://github.com/owner/repo/pull/12>; again"
        " https://gitlab.example/group/project/-/merge_requests/388/diffs and the"
        " commit https://github.com/owner/repo/commit/abc."
    )
    assert [
        request_link.reference
        for request_link in request_links.find_request_links(reply_text)
    ] == ["group/project!388", "owner/repo#12"]


@pytest.mark.parametrize(
    ("origin_url", "repository"),
    [
        (
            "git@gitlab.services.example:team/tools.marketplace.git",
            ("gitlab.services.example", "team/tools.marketplace"),
        ),
        (
            "https://gitlab.services.example/team/tools.marketplace.git",
            ("gitlab.services.example", "team/tools.marketplace"),
        ),
        (
            "ssh://git@gitlab.services.example:2222/team/Tools.Marketplace",
            ("gitlab.services.example", "team/Tools.Marketplace"),
        ),
    ],
)
def test_origin_repository_reads_ssh_and_https_remotes(origin_url, repository):
    origin = MagicMock(returncode=0, stdout=f"{origin_url}\n")
    with patch("request_links.run_command", return_value=origin):
        assert request_links.origin_repository(
            request_links.Path("/any")
        ) == request_links.ForgeRepository(*repository)


def make_clone(directory, origin_project_path, origins):
    (directory / ".git").mkdir(parents=True)
    origins[directory] = origin_project_path


@pytest.fixture
def clone_roots(tmp_path, monkeypatch):
    repositories_root = tmp_path / "repo"
    repositories_root.mkdir()
    monkeypatch.setattr(
        request_links, "LOCAL_CLONE_ROOTS", (repositories_root, tmp_path)
    )
    monkeypatch.chdir(tmp_path)
    origins = {}
    monkeypatch.setattr(
        request_links,
        "origin_repository",
        lambda directory: (
            request_links.ForgeRepository("forge.example", origins[directory])
            if directory in origins
            else None
        ),
    )
    return repositories_root, origins


def test_finds_a_clone_whose_directory_name_differs_from_the_project(clone_roots):
    repositories_root, origins = clone_roots
    make_clone(repositories_root / "other", "group/other", origins)
    make_clone(repositories_root / "marketplace-clone", "group/marketplace", origins)
    assert (
        request_links.find_local_clone("Group/Marketplace")
        == repositories_root / "marketplace-clone"
    )


def test_missing_clone_names_the_project_and_searched_roots(clone_roots):
    with pytest.raises(ReviewTargetError, match="no local clone of group/absent"):
        request_links.find_local_clone("group/absent")


def test_entering_a_repository_moves_into_its_clone(clone_roots):
    repositories_root, origins = clone_roots
    make_clone(repositories_root / "project", "group/project", origins)
    request_links.enter_local_clone(
        request_links.ForgeRepository("gitlab.example", "group/project")
    )
    assert os.getcwd() == str((repositories_root / "project").resolve())


def test_a_subdirectory_of_the_wanted_clone_stays_where_it_is(
    clone_roots, tmp_path, monkeypatch
):
    repositories_root, origins = clone_roots
    make_clone(repositories_root / "project", "group/project", origins)
    origins[request_links.Path.cwd()] = "group/project"
    request_links.enter_local_clone(
        request_links.ForgeRepository("gitlab.example", "group/project")
    )
    assert os.getcwd() == str(tmp_path.resolve())
