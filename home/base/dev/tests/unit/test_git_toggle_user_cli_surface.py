from unittest.mock import patch

import git_toggle_user


class TestGetRepositoryCommitCount:
    def test_returns_count_from_rev_list(self):
        with patch("git_toggle_user.run_git_command", return_value="42"):
            assert git_toggle_user.get_repository_commit_count() == 42

    def test_returns_zero_on_invalid_output(self):
        with patch("git_toggle_user.run_git_command", return_value=""):
            assert git_toggle_user.get_repository_commit_count() == 0

    def test_returns_zero_on_non_numeric_output(self):
        with patch("git_toggle_user.run_git_command", return_value="fatal: error"):
            assert git_toggle_user.get_repository_commit_count() == 0


class TestParseArguments:
    def test_no_args_returns_false(self):
        assert git_toggle_user.parse_arguments([]) is False

    def test_status_flag_returns_true(self):
        assert git_toggle_user.parse_arguments(["--status"]) is True

    def test_short_status_flag_returns_true(self):
        assert git_toggle_user.parse_arguments(["-s"]) is True

    def test_help_flag_exits_zero(self):
        try:
            git_toggle_user.parse_arguments(["--help"])
            assert False, "Should have raised SystemExit"
        except SystemExit as e:
            assert e.code == 0

    def test_short_help_flag_exits_zero(self):
        try:
            git_toggle_user.parse_arguments(["-h"])
            assert False, "Should have raised SystemExit"
        except SystemExit as e:
            assert e.code == 0

    def test_unknown_option_exits_one(self):
        try:
            git_toggle_user.parse_arguments(["--bogus"])
            assert False, "Should have raised SystemExit"
        except SystemExit as e:
            assert e.code == 1


class TestPrintCurrentStatus:
    def test_prints_config_level_and_user(self, capsys):
        git_toggle_user.print_current_status("LOCAL", "Test User", "test@example.com")
        output = capsys.readouterr().out
        assert "LOCAL" in output
        assert "Test User" in output
        assert "test@example.com" in output


class TestPrintUsage:
    def test_prints_usage_info(self, capsys):
        git_toggle_user.print_usage()
        output = capsys.readouterr().out
        assert "git-toggle-user" in output
        assert "--status" in output
        assert "--help" in output
        assert git_toggle_user.WORK_EMAIL in output
        assert git_toggle_user.PERSONAL_EMAIL in output
