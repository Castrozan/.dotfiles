import subprocess
from pathlib import Path

import pytest

import forge_adapter
from forge.repository import Repository
from forge_adapter import ForgeAdapter, ForgeUnavailable


@pytest.fixture
def github_repository(monkeypatch):
    monkeypatch.setattr(
        forge_adapter,
        "resolve_repository",
        lambda _: Repository("github", "github.com", "owner/repository"),
    )


def test_only_group_branches_count_as_the_watchers_pull_requests(
    github_repository, monkeypatch
):
    listed = '[{"number":1,"headRefName":"ril-group-a","comments":[]},{"number":2,"headRefName":"feature-b","comments":[]}]'
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_, **__: subprocess.CompletedProcess([], 0, listed, ""),
    )

    pull_requests = ForgeAdapter(Path("/repo")).open_pull_requests("ril-group-")

    assert [pull_request["number"] for pull_request in pull_requests] == [1]


def test_a_failed_lookup_raises_rather_than_reporting_no_pull_requests(
    github_repository, monkeypatch
):
    def unavailable(*arguments, **options):
        raise subprocess.CalledProcessError(
            1, arguments, stderr="gh: not authenticated"
        )

    monkeypatch.setattr(subprocess, "run", unavailable)

    with pytest.raises(ForgeUnavailable):
        ForgeAdapter(Path("/repo")).open_pull_requests("ril-group-")
