import os
import subprocess

import pytest

import deploy_github_authentication


def test_replaces_stale_native_credentials_without_exposing_token(
    tmp_path, monkeypatch, capsys
):
    token_file = tmp_path / "github-token"
    token_file.write_text("deployed-secret\n")
    credential_file = tmp_path / "gh" / "hosts.yml"
    credential_file.parent.mkdir()
    credential_file.write_text("github.com:\n  oauth_token: stale-token\n")
    monkeypatch.setenv("GH_TOKEN", "temporary-token")
    monkeypatch.setenv("GITHUB_TOKEN", "temporary-github-token")
    monkeypatch.setenv("GH_ENTERPRISE_TOKEN", "enterprise-token")
    calls = []

    def run(command, **options):
        calls.append((command, options))

    monkeypatch.setattr(subprocess, "run", run)

    deploy_github_authentication.deploy_github_authentication(
        "gh", token_file, credential_file
    )

    assert len(calls) == 1
    command, options = calls[0]
    assert command == [
        "gh",
        "auth",
        "login",
        "--hostname",
        "github.com",
        "--git-protocol",
        "ssh",
        "--skip-ssh-key",
        "--insecure-storage",
        "--with-token",
    ]
    assert options["input"] == "deployed-secret\n"
    assert options["timeout"] == 30
    assert options["check"]
    assert "GH_TOKEN" not in options["env"]
    assert "GITHUB_TOKEN" not in options["env"]
    assert options["env"]["GH_ENTERPRISE_TOKEN"] == "enterprise-token"
    assert options["env"]["GH_CONFIG_DIR"] == str(credential_file.parent)
    assert os.environ["GH_TOKEN"] == "temporary-token"
    assert "secret" not in capsys.readouterr().out


def test_matching_native_file_credential_skips_login(tmp_path, monkeypatch):
    token_file = tmp_path / "github-token"
    token_file.write_text("deployed-secret\n")
    credential_file = tmp_path / "hosts.yml"
    credential_file.write_text("github.com:\n  oauth_token: deployed-secret\n")
    credential_modified_at = credential_file.stat().st_mtime_ns
    calls = []

    def run(command, **options):
        calls.append(command)

    monkeypatch.setattr(subprocess, "run", run)

    deploy_github_authentication.deploy_github_authentication(
        "gh", token_file, credential_file
    )

    assert calls == []
    assert credential_file.stat().st_mtime_ns == credential_modified_at


def test_matching_keyring_credential_is_migrated_for_headless_access(
    tmp_path, monkeypatch, capsys
):
    token_file = tmp_path / "github-token"
    token_file.write_text("deployed-secret\n")
    credential_file = tmp_path / "hosts.yml"
    credential_file.write_text("github.com:\n  user: Castrozan\n  git_protocol: ssh\n")
    calls = []

    def run(command, **options):
        calls.append(command)

    monkeypatch.setattr(subprocess, "run", run)

    deploy_github_authentication.deploy_github_authentication(
        "gh", token_file, credential_file
    )

    assert len(calls) == 1
    assert "--insecure-storage" in calls[0]
    assert "deployed-secret" not in capsys.readouterr().out


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
            "gh", tmp_path / "missing", tmp_path / "hosts.yml"
        )

    assert calls == []


def test_login_failure_is_reported_without_retry(tmp_path, monkeypatch):
    token_file = tmp_path / "github-token"
    token_file.write_text("deployed-secret\n")
    calls = []

    def run(command, **options):
        calls.append(command)
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(subprocess, "run", run)

    with pytest.raises(subprocess.CalledProcessError):
        deploy_github_authentication.deploy_github_authentication(
            "gh", token_file, tmp_path / "hosts.yml"
        )

    assert len(calls) == 1


@pytest.mark.parametrize(
    "configuration",
    [
        "github.com:\n  oauth_token: sensitive-value:\n",
        "[sensitive-value]\n",
        "github.com: [sensitive-value]\n",
    ],
)
def test_malformed_credentials_fail_without_disclosing_or_overwriting_content(
    tmp_path, monkeypatch, configuration
):
    token_file = tmp_path / "github-token"
    token_file.write_text("deployed-secret\n")
    credential_file = tmp_path / "hosts.yml"
    credential_file.write_text(configuration)
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: calls.append(args))

    with pytest.raises(ValueError) as exception:
        deploy_github_authentication.deploy_github_authentication(
            "gh", token_file, credential_file
        )

    assert str(exception.value) == "GitHub CLI authentication file is malformed"
    assert credential_file.read_text() == configuration
    assert calls == []
