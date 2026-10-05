import os
import subprocess
from types import SimpleNamespace

import pytest

import deploy_github_authentication


def test_replaces_stale_native_credentials_without_exposing_token(
    tmp_path, monkeypatch, capsys
):
    token_file = tmp_path / "github-token"
    token_file.write_text("deployed-secret\n")
    monkeypatch.setenv("GH_TOKEN", "temporary-token")
    monkeypatch.setenv("GITHUB_TOKEN", "temporary-github-token")
    monkeypatch.setenv("GH_ENTERPRISE_TOKEN", "enterprise-token")
    calls = []

    def run(command, **options):
        calls.append((command, options))
        return SimpleNamespace(returncode=0, stdout="stale-token\n")

    monkeypatch.setattr(subprocess, "run", run)

    deploy_github_authentication.deploy_github_authentication("gh", token_file)

    command, options = calls[1]
    assert command == [
        "gh",
        "auth",
        "login",
        "--hostname",
        "github.com",
        "--git-protocol",
        "ssh",
        "--skip-ssh-key",
        "--with-token",
    ]
    assert options["input"] == "deployed-secret\n"
    assert options["timeout"] == 30
    assert options["check"]
    assert "GH_TOKEN" not in options["env"]
    assert "GITHUB_TOKEN" not in options["env"]
    assert options["env"]["GH_ENTERPRISE_TOKEN"] == "enterprise-token"
    assert os.environ["GH_TOKEN"] == "temporary-token"
    assert "secret" not in capsys.readouterr().out


def test_matching_native_credential_skips_login(tmp_path, monkeypatch):
    token_file = tmp_path / "github-token"
    token_file.write_text("deployed-secret\n")
    calls = []

    def run(command, **options):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout="deployed-secret\n")

    monkeypatch.setattr(subprocess, "run", run)

    deploy_github_authentication.deploy_github_authentication("gh", token_file)

    assert calls == [["gh", "auth", "token", "--hostname", "github.com"]]


def test_missing_secret_fails_after_bounded_wait_before_native_auth(
    tmp_path, monkeypatch
):
    clock = iter([0.0, 31.0])
    monkeypatch.setattr(
        deploy_github_authentication.time, "monotonic", lambda: next(clock)
    )
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: calls.append(args))

    with pytest.raises(TimeoutError, match="GitHub credential did not materialize"):
        deploy_github_authentication.deploy_github_authentication(
            "gh", tmp_path / "missing"
        )

    assert calls == []


def test_login_failure_is_reported_without_retry(tmp_path, monkeypatch):
    token_file = tmp_path / "github-token"
    token_file.write_text("deployed-secret\n")
    calls = []

    def run(command, **options):
        calls.append(command)
        if command[2] == "login":
            raise subprocess.CalledProcessError(1, command)
        return SimpleNamespace(returncode=1, stdout="")

    monkeypatch.setattr(subprocess, "run", run)

    with pytest.raises(subprocess.CalledProcessError):
        deploy_github_authentication.deploy_github_authentication("gh", token_file)

    assert len(calls) == 2
