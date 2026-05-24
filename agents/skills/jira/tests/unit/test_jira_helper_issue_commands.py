from unittest.mock import patch

from jira_test_helpers import jira_helper, make_successful_subprocess_result


class TestViewIssue:
    @patch("subprocess.run")
    def test_prints_issue_output(self, mock_run, capsys):
        mock_run.return_value = make_successful_subprocess_result(
            stdout="CAFE-498 | Tiered permissions | To Do\n"
        )
        jira_helper.view_issue("CAFE-498")
        output = capsys.readouterr().out
        assert "CAFE-498" in output
        assert "Tiered permissions" in output


class TestListIssues:
    @patch("subprocess.run")
    def test_list_with_no_filters(self, mock_run, capsys):
        mock_run.return_value = make_successful_subprocess_result(
            stdout="issue list output\n"
        )
        jira_helper.list_issues()
        called_command = mock_run.call_args[0][0]
        assert "jira" in called_command
        assert "issue" in called_command
        assert "list" in called_command
        assert "--plain" in called_command
        assert "--no-input" in called_command

    @patch("subprocess.run")
    def test_list_with_all_filters(self, mock_run, capsys):
        mock_run.return_value = make_successful_subprocess_result(stdout="filtered\n")
        jira_helper.list_issues(
            project="CAFE",
            status="To Do",
            issue_type="Story",
            assignee="lucas",
            label="backend",
            jql_query="priority = High",
            columns="KEY,STATUS,SUMMARY",
        )
        called_command = mock_run.call_args[0][0]
        assert "--project" in called_command
        assert "CAFE" in called_command
        assert "-s" in called_command
        assert "To Do" in called_command
        assert "--type" in called_command
        assert "Story" in called_command
        assert "-a" in called_command
        assert "lucas" in called_command
        assert "--label" in called_command
        assert "-q" in called_command
        assert "--columns" in called_command


class TestCreateIssue:
    @patch("subprocess.run")
    def test_creates_issue_with_required_fields(self, mock_run, capsys):
        mock_run.return_value = make_successful_subprocess_result(
            stdout="CAFE-500 created\n"
        )
        jira_helper.create_issue(summary="New feature")
        called_command = mock_run.call_args[0][0]
        assert "-t" in called_command
        assert "Task" in called_command
        assert "-s" in called_command
        assert "New feature" in called_command
        assert "--no-input" in called_command

    @patch("subprocess.run")
    def test_creates_issue_with_all_optional_fields(self, mock_run, capsys):
        mock_run.return_value = make_successful_subprocess_result(
            stdout="CAFE-501 created\n"
        )
        jira_helper.create_issue(
            summary="Bug report",
            issue_type="Bug",
            description="Something broke",
            assignee="lucas",
            priority="High",
            labels="urgent",
            parent="CAFE-100",
        )
        called_command = mock_run.call_args[0][0]
        assert "Bug" in called_command
        assert "-b" in called_command
        assert "Something broke" in called_command
        assert "-a" in called_command
        assert "lucas" in called_command
        assert "-y" in called_command
        assert "High" in called_command
        assert "-l" in called_command
        assert "-P" in called_command
        assert "CAFE-100" in called_command


class TestMoveIssue:
    @patch("subprocess.run")
    def test_moves_issue_to_target_status(self, mock_run, capsys):
        mock_run.return_value = make_successful_subprocess_result(stdout="moved\n")
        jira_helper.move_issue("CAFE-498", "In Progress")
        called_command = mock_run.call_args[0][0]
        assert "move" in called_command
        assert "CAFE-498" in called_command
        assert "In Progress" in called_command

    @patch("subprocess.run")
    def test_moves_issue_with_comment_and_assignee(self, mock_run, capsys):
        mock_run.return_value = make_successful_subprocess_result(stdout="moved\n")
        jira_helper.move_issue("CAFE-498", "Done", comment="Finished", assignee="lucas")
        called_command = mock_run.call_args[0][0]
        assert "--comment" in called_command
        assert "Finished" in called_command
        assert "-a" in called_command
        assert "lucas" in called_command


class TestEditIssue:
    @patch("subprocess.run")
    def test_edits_issue_summary(self, mock_run, capsys):
        mock_run.return_value = make_successful_subprocess_result(stdout="updated\n")
        jira_helper.edit_issue("CAFE-498", summary="Updated title")
        called_command = mock_run.call_args[0][0]
        assert "edit" in called_command
        assert "CAFE-498" in called_command
        assert "-s" in called_command
        assert "Updated title" in called_command


class TestAddComment:
    @patch("subprocess.run")
    def test_adds_comment_to_issue(self, mock_run, capsys):
        mock_run.return_value = make_successful_subprocess_result(
            stdout="comment added\n"
        )
        jira_helper.add_comment("CAFE-498", "Looking into this")
        called_command = mock_run.call_args[0][0]
        assert "comment" in called_command
        assert "add" in called_command
        assert "CAFE-498" in called_command
        assert "-b" in called_command
        assert "Looking into this" in called_command


class TestLogWork:
    @patch("subprocess.run")
    def test_logs_time_with_comment(self, mock_run, capsys):
        mock_run.return_value = make_successful_subprocess_result(stdout="logged\n")
        jira_helper.log_work("CAFE-498", "2h", comment="Research")
        called_command = mock_run.call_args[0][0]
        assert "worklog" in called_command
        assert "CAFE-498" in called_command
        assert "2h" in called_command
        assert "--comment" in called_command
        assert "Research" in called_command


class TestOpenInBrowser:
    @patch("subprocess.run")
    def test_opens_issue_without_browser(self, mock_run, capsys):
        mock_run.return_value = make_successful_subprocess_result(
            stdout="https://jira.example.com/browse/CAFE-498\n"
        )
        jira_helper.open_in_browser("CAFE-498")
        called_command = mock_run.call_args[0][0]
        assert "open" in called_command
        assert "--no-browser" in called_command


class TestMyIssues:
    @patch("subprocess.run")
    def test_lists_my_issues(self, mock_run, capsys):
        mock_run.return_value = make_successful_subprocess_result(stdout="my issues\n")
        jira_helper.my_issues()
        called_command = mock_run.call_args[0][0]
        assert "jira me" in called_command

    @patch("subprocess.run")
    def test_lists_my_issues_with_status_filter(self, mock_run, capsys):
        mock_run.return_value = make_successful_subprocess_result(stdout="filtered\n")
        jira_helper.my_issues(status="In Progress")
        called_command = mock_run.call_args[0][0]
        assert "In Progress" in called_command
