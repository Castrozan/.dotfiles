import subprocess

import pytest

from forge import repository


@pytest.mark.parametrize(
    "remote,hostname,project",
    [
        (
            "https://gitlab.com/team/subgroup/project.git",
            "gitlab.com",
            "team/subgroup/project",
        ),
        ("git@github.com:owner/project.git", "github.com", "owner/project"),
        ("ssh://git@git.example/team/project", "git.example", "team/project"),
    ],
)
def test_remote_namespace_is_preserved(remote, hostname, project):
    assert repository.parse_remote(remote) == (hostname, project)


@pytest.mark.parametrize(
    "remote",
    [
        "/tmp/repository",
        "https://gitlab.com/project",
        "https://gitlab.com/a/../b",
        "file:///tmp/a/b",
    ],
)
def test_unsupported_remote_is_rejected(remote):
    with pytest.raises(ValueError):
        repository.parse_remote(remote)


def test_effective_upstream_uses_git_rewrites_and_remote_names_with_slashes(tmp_path):
    def git(*arguments):
        return subprocess.run(
            ["git", *arguments],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=True,
        )

    git("init", "-b", "topic")
    git("remote", "add", "team/upstream", "https://github.com/owner/project.git")
    git("config", "branch.topic.remote", "team/upstream")
    git(
        "config", "url.https://gitlab.com/owner/.insteadOf", "https://github.com/owner/"
    )
    result = repository.resolve_repository(tmp_path)

    assert result == repository.Repository("gitlab", "gitlab.com", "owner/project")


def test_ssh_alias_is_resolved_before_provider_selection(monkeypatch, tmp_path):
    calls = []

    def execute(command, directory):
        calls.append(command)
        response = (
            "hostname gitlab.services.betha.cloud\n"
            if command[0] == "ssh"
            else "gitlab.services.betha.cloud\n"
        )
        return subprocess.CompletedProcess(command, 0, response)

    monkeypatch.setattr(repository, "execute", execute)
    result = repository.resolve_repository(tmp_path, "git@gitlab.com:group/project.git")

    assert result.hostname == "gitlab.services.betha.cloud"
    assert calls[0] == ["ssh", "-G", "gitlab.com"]
    assert calls[1][-1] == "gitlab.services.betha.cloud"


def test_https_does_not_use_ssh_alias(monkeypatch):
    monkeypatch.setattr(
        repository,
        "execute",
        lambda *arguments: pytest.fail("SSH aliases cannot change HTTPS"),
    )
    assert (
        repository.resolve_repository(
            repository="https://gitlab.com/owner/project"
        ).hostname
        == "gitlab.com"
    )


def test_unknown_host_requires_explicit_provider(monkeypatch):
    monkeypatch.setattr(
        repository,
        "execute",
        lambda command, directory: subprocess.CompletedProcess(
            command, 1, "", "unregistered"
        ),
    )
    with pytest.raises(ValueError, match="Unrecognized"):
        repository.resolve_repository(
            repository="https://unknown.example/owner/project"
        )
    assert (
        repository.resolve_repository(
            repository="https://unknown.example/owner/project", provider="github"
        ).provider
        == "github"
    )


def test_github_enterprise_uses_native_host_registration(monkeypatch):
    def execute(command, directory):
        response = '{"hosts":{"github.example":[]}}' if command[0] == "gh" else ""
        return subprocess.CompletedProcess(command, 0, response)

    monkeypatch.setattr(repository, "execute", execute)
    assert (
        repository.resolve_repository(
            repository="https://github.example/owner/project"
        ).provider
        == "github"
    )
