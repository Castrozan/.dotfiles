import subprocess
from types import SimpleNamespace
from urllib.error import URLError

import pytest

import refresh_gitlab_contribution_heatmap as refresh


@pytest.fixture
def token_file(tmp_path):
    path = tmp_path / "gitlab-token"
    path.write_text("gitlab-secret\n")
    return path


@pytest.fixture
def reachable_gitlab(monkeypatch):
    requests = []

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *exception):
            return False

    def urlopen(request, timeout):
        requests.append(request)
        return Response()

    monkeypatch.setattr(refresh, "urlopen", urlopen)
    return requests


def record_commands(monkeypatch, graphs_differ):
    commands = []

    def run(command, **options):
        commands.append(command)
        if command[3:5] == ["diff", "--quiet"]:
            return SimpleNamespace(returncode=1 if graphs_differ else 0)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", run)
    return commands


def arguments_for(token_file, checkout):
    return [
        "--gitlab-url",
        "https://gitlab.example",
        "--gitlab-token-file",
        str(token_file),
        "--checkout",
        str(checkout),
    ]


def test_changed_graphs_are_published_before_the_profile_is_recorded(
    tmp_path, token_file, reachable_gitlab, monkeypatch
):
    checkout = tmp_path / "exporter"
    commands = record_commands(monkeypatch, graphs_differ=True)

    refresh.main(arguments_for(token_file, checkout))

    assert reachable_gitlab[0].full_url == "https://gitlab.example/api/v4/user"
    assert reachable_gitlab[0].get_header("Private-token") == "gitlab-secret"
    assert commands[0][:3] == ["git", "clone", "--quiet"]
    subcommands = [command[3] for command in commands if command[:2] == ["git", "-C"]]
    assert subcommands[-3:] == ["add", "commit", "push"]
    assert commands[-1][:3] == ["gh", "workflow", "run"]
    assert "Castrozan/Castrozan" in commands[-1]


def test_unchanged_graphs_neither_commit_nor_record_the_profile(
    tmp_path, token_file, reachable_gitlab, monkeypatch
):
    checkout = tmp_path / "exporter"
    (checkout / ".git").mkdir(parents=True)
    commands = record_commands(monkeypatch, graphs_differ=False)

    refresh.main(arguments_for(token_file, checkout))

    assert not any(command[1] == "clone" for command in commands)
    assert not any("commit" in command or "push" in command for command in commands)
    assert not any(command[0] == "gh" for command in commands)


def test_generator_receives_the_gitlab_credentials(
    tmp_path, token_file, reachable_gitlab, monkeypatch
):
    environments = []

    def run(command, **options):
        if options.get("env"):
            environments.append(options["env"])
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", run)

    refresh.main(arguments_for(token_file, tmp_path / "exporter"))

    assert environments[0]["GITLAB_URL"] == "https://gitlab.example"
    assert environments[0]["GITLAB_TOKEN"] == token_file.read_text().strip()


def test_non_https_gitlab_url_is_refused_before_any_request(
    tmp_path, token_file, reachable_gitlab, monkeypatch
):
    commands = record_commands(monkeypatch, graphs_differ=True)
    arguments = arguments_for(token_file, tmp_path / "exporter")
    arguments[1] = "file:///etc/passwd"

    with pytest.raises(ValueError):
        refresh.main(arguments)

    assert reachable_gitlab == []
    assert commands == []


def test_unreachable_gitlab_fails_before_touching_the_checkout(
    tmp_path, token_file, monkeypatch
):
    def urlopen(request, timeout):
        raise URLError("no route to host")

    monkeypatch.setattr(refresh, "urlopen", urlopen)
    commands = record_commands(monkeypatch, graphs_differ=True)

    with pytest.raises(URLError):
        refresh.main(arguments_for(token_file, tmp_path / "exporter"))

    assert commands == []
