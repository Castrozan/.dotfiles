from unittest.mock import patch

import pytest

from jira_test_helpers import (
    jira_helper,
    make_failed_subprocess_result,
    make_successful_subprocess_result,
)


class TestRunJiraCommand:
    @patch("subprocess.run")
    def test_constructs_command_with_jira_prefix(self, mock_run):
        mock_run.return_value = make_successful_subprocess_result(stdout="ok")
        jira_helper.run_jira_command(["issue", "view", "CAFE-498"])
        called_command = mock_run.call_args[0][0]
        assert called_command == ["jira", "issue", "view", "CAFE-498"]

    @patch("subprocess.run")
    def test_exits_on_error_when_output_expected(self, mock_run):
        mock_run.return_value = make_failed_subprocess_result(stderr="not found")
        with pytest.raises(SystemExit):
            jira_helper.run_jira_command(["issue", "view", "NONEXISTENT"])

    @patch("subprocess.run")
    def test_does_not_exit_on_error_when_output_not_expected(self, mock_run):
        mock_run.return_value = make_failed_subprocess_result(stderr="warning")
        result = jira_helper.run_jira_command(
            ["issue", "view", "X-1"], expect_output=False
        )
        assert result.returncode == 1
