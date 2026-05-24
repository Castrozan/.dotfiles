from unittest.mock import patch

import git_toggle_user


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
