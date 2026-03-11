from unittest.mock import patch, MagicMock

import git_toggle_user


class TestRunGitCommand:
    def test_returns_stripped_stdout(self):
        mock_result = MagicMock()
        mock_result.stdout = "  some output  \n"
        with patch("git_toggle_user.subprocess.run", return_value=mock_result):
            assert (
                git_toggle_user.run_git_command(["config", "user.name"])
                == "some output"
            )

    def test_passes_git_prefix_and_args(self):
        mock_result = MagicMock()
        mock_result.stdout = ""
        with patch(
            "git_toggle_user.subprocess.run", return_value=mock_result
        ) as mock_run:
            git_toggle_user.run_git_command(["status"])
            mock_run.assert_called_once_with(
                ["git", "status"], capture_output=True, text=True
            )


class TestIsInsideGitRepository:
    def test_returns_true_when_inside_repo(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("git_toggle_user.subprocess.run", return_value=mock_result):
            assert git_toggle_user.is_inside_git_repository() is True

    def test_returns_false_when_outside_repo(self):
        mock_result = MagicMock()
        mock_result.returncode = 128
        with patch("git_toggle_user.subprocess.run", return_value=mock_result):
            assert git_toggle_user.is_inside_git_repository() is False


class TestGetCurrentGitUser:
    def test_returns_local_config_when_set(self):
        def mock_run_git(args):
            if args == ["config", "--local", "user.name"]:
                return "Local Name"
            if args == ["config", "--local", "user.email"]:
                return "local@example.com"
            return ""

        with patch("git_toggle_user.run_git_command", side_effect=mock_run_git):
            level, name, email = git_toggle_user.get_current_git_user()
            assert level == "LOCAL"
            assert name == "Local Name"
            assert email == "local@example.com"

    def test_falls_back_to_global_when_local_not_set(self):
        def mock_run_git(args):
            if args == ["config", "--local", "user.name"]:
                return ""
            if args == ["config", "--local", "user.email"]:
                return ""
            if args == ["config", "--global", "user.name"]:
                return "Global Name"
            if args == ["config", "--global", "user.email"]:
                return "global@example.com"
            return ""

        with patch("git_toggle_user.run_git_command", side_effect=mock_run_git):
            level, name, email = git_toggle_user.get_current_git_user()
            assert level == "GLOBAL"
            assert name == "Global Name"
            assert email == "global@example.com"

    def test_uses_defaults_when_global_not_set(self):
        with patch("git_toggle_user.run_git_command", return_value=""):
            level, name, email = git_toggle_user.get_current_git_user()
            assert level == "GLOBAL"
            assert name == "Unknown"
            assert email == "unknown@example.com"


class TestSetLocalGitUser:
    def test_calls_git_config_local(self):
        with patch("git_toggle_user.subprocess.run") as mock_run:
            git_toggle_user.set_local_git_user("Test Name", "test@example.com")
            assert mock_run.call_count == 2
            mock_run.assert_any_call(
                ["git", "config", "--local", "user.name", "Test Name"]
            )
            mock_run.assert_any_call(
                ["git", "config", "--local", "user.email", "test@example.com"]
            )


class TestDetermineTargetUser:
    def test_switches_from_work_to_personal(self):
        target_type, name, email = git_toggle_user.determine_target_user(
            git_toggle_user.WORK_EMAIL
        )
        assert target_type == "PERSONAL"
        assert name == git_toggle_user.PERSONAL_NAME
        assert email == git_toggle_user.PERSONAL_EMAIL

    def test_switches_from_personal_to_work(self):
        target_type, name, email = git_toggle_user.determine_target_user(
            git_toggle_user.PERSONAL_EMAIL
        )
        assert target_type == "WORK"
        assert name == git_toggle_user.WORK_NAME
        assert email == git_toggle_user.WORK_EMAIL

    def test_defaults_to_personal_for_unknown_email(self):
        target_type, name, email = git_toggle_user.determine_target_user(
            "unknown@example.com"
        )
        assert target_type == "PERSONAL"
        assert name == git_toggle_user.PERSONAL_NAME
        assert email == git_toggle_user.PERSONAL_EMAIL


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


class TestMain:
    def test_exits_when_not_in_git_repo(self):
        with patch("git_toggle_user.is_inside_git_repository", return_value=False):
            try:
                git_toggle_user.main()
                assert False, "Should have raised SystemExit"
            except SystemExit as e:
                assert e.code == 1

    def test_status_only_does_not_toggle(self):
        with patch("git_toggle_user.sys.argv", ["cmd", "--status"]):
            with patch("git_toggle_user.is_inside_git_repository", return_value=True):
                with patch(
                    "git_toggle_user.get_current_git_user",
                    return_value=("LOCAL", "Test", "test@example.com"),
                ):
                    with patch("git_toggle_user.set_local_git_user") as mock_set:
                        git_toggle_user.main()
                        mock_set.assert_not_called()

    def test_toggles_user_when_no_flags(self):
        with patch("git_toggle_user.sys.argv", ["cmd"]):
            with patch("git_toggle_user.is_inside_git_repository", return_value=True):
                with patch(
                    "git_toggle_user.get_current_git_user",
                    return_value=(
                        "LOCAL",
                        git_toggle_user.WORK_NAME,
                        git_toggle_user.WORK_EMAIL,
                    ),
                ):
                    with patch("git_toggle_user.set_local_git_user") as mock_set:
                        with patch(
                            "git_toggle_user.get_repository_commit_count",
                            return_value=0,
                        ):
                            git_toggle_user.main()
                            mock_set.assert_called_once_with(
                                git_toggle_user.PERSONAL_NAME,
                                git_toggle_user.PERSONAL_EMAIL,
                            )

    def test_shows_commit_warning_when_commits_exist(self, capsys):
        with patch("git_toggle_user.sys.argv", ["cmd"]):
            with patch("git_toggle_user.is_inside_git_repository", return_value=True):
                with patch(
                    "git_toggle_user.get_current_git_user",
                    return_value=(
                        "GLOBAL",
                        "Unknown",
                        "unknown@example.com",
                    ),
                ):
                    with patch("git_toggle_user.set_local_git_user"):
                        with patch(
                            "git_toggle_user.get_repository_commit_count",
                            return_value=10,
                        ):
                            git_toggle_user.main()
                            output = capsys.readouterr().out
                            assert "future commits" in output
