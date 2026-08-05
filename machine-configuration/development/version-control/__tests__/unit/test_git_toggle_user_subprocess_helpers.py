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
