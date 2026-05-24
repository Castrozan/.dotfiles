from unittest.mock import MagicMock, patch

import pytest


class TestResolveGitlabHostFromRemoteUrl:
    def test_returns_coates_host_for_ssh_remote(self, glab_harness_module):
        assert (
            glab_harness_module.resolve_gitlab_host_from_remote_url(
                "git@git.coates.io:digital-production/mcdca-tools/mcdca-workspace.git"
            )
            == "git.coates.io"
        )

    def test_returns_gitlab_com_host_for_ssh_remote(self, glab_harness_module):
        assert (
            glab_harness_module.resolve_gitlab_host_from_remote_url(
                "git@gitlab.com:coates/mcd-ca/shell.git"
            )
            == "gitlab.com"
        )

    def test_returns_host_for_https_remote(self, glab_harness_module):
        assert (
            glab_harness_module.resolve_gitlab_host_from_remote_url(
                "https://gitlab.com/coates/mcd-ca/tools/digital-promo-scaffolding.git"
            )
            == "gitlab.com"
        )

    def test_exits_for_unsupported_host(self, glab_harness_module):
        with pytest.raises(SystemExit):
            glab_harness_module.resolve_gitlab_host_from_remote_url(
                "git@github.com:foo/bar.git"
            )


class TestResolveGitlabToken:
    def test_returns_coates_token_from_environment(
        self, monkeypatch, glab_harness_module
    ):
        monkeypatch.setenv("GITLAB_TOKEN", "env-coates-token")
        assert (
            glab_harness_module.resolve_gitlab_token("git.coates.io")
            == "env-coates-token"
        )

    def test_returns_gitlab_com_token_from_environment(
        self, monkeypatch, glab_harness_module
    ):
        monkeypatch.setenv("GITLAB_COM_TOKEN", "env-com-token")
        assert glab_harness_module.resolve_gitlab_token("gitlab.com") == "env-com-token"

    def test_exits_when_no_token_and_no_secret_file(
        self, monkeypatch, tmp_path, glab_harness_module
    ):
        monkeypatch.delenv("GITLAB_TOKEN", raising=False)
        monkeypatch.setitem(
            glab_harness_module.GITLAB_TOKEN_SECRET_FILE_PATH_BY_HOST,
            "git.coates.io",
            tmp_path / "does-not-exist",
        )
        with pytest.raises(SystemExit):
            glab_harness_module.resolve_gitlab_token("git.coates.io")

    def test_reads_coates_token_from_secret_file(
        self, monkeypatch, tmp_path, glab_harness_module
    ):
        monkeypatch.delenv("GITLAB_TOKEN", raising=False)
        secret_file = tmp_path / "glab-token"
        secret_file.write_text("token-from-disk\n")
        monkeypatch.setitem(
            glab_harness_module.GITLAB_TOKEN_SECRET_FILE_PATH_BY_HOST,
            "git.coates.io",
            secret_file,
        )
        assert (
            glab_harness_module.resolve_gitlab_token("git.coates.io")
            == "token-from-disk"
        )

    def test_reads_gitlab_com_token_from_secret_file(
        self, monkeypatch, tmp_path, glab_harness_module
    ):
        monkeypatch.delenv("GITLAB_COM_TOKEN", raising=False)
        secret_file = tmp_path / "gitlab-com-token"
        secret_file.write_text("com-token-from-disk\n")
        monkeypatch.setitem(
            glab_harness_module.GITLAB_TOKEN_SECRET_FILE_PATH_BY_HOST,
            "gitlab.com",
            secret_file,
        )
        assert (
            glab_harness_module.resolve_gitlab_token("gitlab.com")
            == "com-token-from-disk"
        )


class TestResolveProjectPathFromRemoteUrl:
    def test_parses_ssh_coates_remote_url(self, glab_harness_module):
        assert (
            glab_harness_module.resolve_project_path_from_remote_url(
                "git@git.coates.io:digital-production/mcdca-tools/mcdca-workspace.git"
            )
            == "digital-production/mcdca-tools/mcdca-workspace"
        )

    def test_parses_ssh_gitlab_com_remote_url(self, glab_harness_module):
        assert (
            glab_harness_module.resolve_project_path_from_remote_url(
                "git@gitlab.com:coates/mcd-ca/tools/digital-promo-scaffolding.git"
            )
            == "coates/mcd-ca/tools/digital-promo-scaffolding"
        )

    def test_parses_https_remote_url(self, glab_harness_module):
        assert (
            glab_harness_module.resolve_project_path_from_remote_url(
                "https://gitlab.com/coates/mcd-ca/shell.git"
            )
            == "coates/mcd-ca/shell"
        )


class TestResolveGitRemoteUrl:
    @patch("subprocess.run")
    def test_exits_when_not_a_git_repo(self, mock_run, glab_harness_module):
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="not a git repo"
        )
        with pytest.raises(SystemExit):
            glab_harness_module.resolve_git_remote_url()
