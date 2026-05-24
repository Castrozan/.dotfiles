from unittest.mock import patch

import git_toggle_user


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
