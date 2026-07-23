import os

import pytest

from jira_test_helpers import jira_helper, jira_helper_authentication


class TestLoadJiraApiTokenIntoEnvironmentIfMissing:
    def test_leaves_existing_environment_variable_untouched(self, monkeypatch):
        monkeypatch.setenv(
            jira_helper.JIRA_API_TOKEN_ENVIRONMENT_VARIABLE_NAME, "preexisting-token"
        )
        jira_helper.load_jira_api_token_into_environment_if_missing()
        assert (
            os.environ[jira_helper.JIRA_API_TOKEN_ENVIRONMENT_VARIABLE_NAME]
            == "preexisting-token"
        )

    def test_reads_token_from_secret_file_when_environment_variable_missing(
        self, monkeypatch, tmp_path
    ):
        monkeypatch.delenv(
            jira_helper.JIRA_API_TOKEN_ENVIRONMENT_VARIABLE_NAME, raising=False
        )
        secret_file = tmp_path / "jira-api-token"
        secret_file.write_text("token-from-disk\n")
        monkeypatch.setattr(
            jira_helper_authentication,
            "JIRA_API_TOKEN_SECRET_FILE_PATH",
            secret_file,
        )
        jira_helper.load_jira_api_token_into_environment_if_missing()
        assert (
            os.environ[jira_helper.JIRA_API_TOKEN_ENVIRONMENT_VARIABLE_NAME]
            == "token-from-disk"
        )

    def test_exits_when_environment_variable_missing_and_secret_file_absent(
        self, monkeypatch, tmp_path
    ):
        monkeypatch.delenv(
            jira_helper.JIRA_API_TOKEN_ENVIRONMENT_VARIABLE_NAME, raising=False
        )
        monkeypatch.setattr(
            jira_helper_authentication,
            "JIRA_API_TOKEN_SECRET_FILE_PATH",
            tmp_path / "does-not-exist",
        )
        with pytest.raises(SystemExit):
            jira_helper.load_jira_api_token_into_environment_if_missing()
