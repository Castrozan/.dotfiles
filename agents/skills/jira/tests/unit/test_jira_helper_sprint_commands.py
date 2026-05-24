from unittest.mock import patch

from jira_test_helpers import jira_helper, make_successful_subprocess_result


class TestListSprints:
    @patch("subprocess.run")
    def test_lists_all_sprints(self, mock_run, capsys):
        mock_run.return_value = make_successful_subprocess_result(
            stdout="Sprint 1\nSprint 2\n"
        )
        jira_helper.list_sprints()
        called_command = mock_run.call_args[0][0]
        assert "sprint" in called_command
        assert "list" in called_command
        assert "--current" not in called_command

    @patch("subprocess.run")
    def test_lists_current_sprint_only(self, mock_run, capsys):
        mock_run.return_value = make_successful_subprocess_result(
            stdout="Current Sprint\n"
        )
        jira_helper.list_sprints(current_only=True)
        called_command = mock_run.call_args[0][0]
        assert "--current" in called_command
