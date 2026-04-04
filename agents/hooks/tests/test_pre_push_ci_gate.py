import json
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

import pre_push_ci_gate as sut


class TestIsGitPushCommand:
    @pytest.mark.parametrize(
        "cmd",
        [
            "git push",
            "git push origin main",
            "git push --force origin main",
            "git -C /tmp push origin main",
            "something && git push",
            "echo ok; git push",
            "test || git push",
        ],
    )
    def test_detects_git_push(self, cmd):
        assert sut.is_git_push_command(cmd) is True

    @pytest.mark.parametrize(
        "cmd",
        [
            "git commit -m 'push stuff'",
            "git pull",
            "git status",
            "echo git push",
            "grep 'git push' file.txt",
            "git log --oneline",
        ],
    )
    def test_ignores_non_push(self, cmd):
        assert sut.is_git_push_command(cmd) is False


class TestIsDotfilesRepo:
    def test_matches_dotfiles(self):
        assert sut.is_dotfiles_repo("/home/user/.dotfiles") is True

    def test_rejects_other_repos(self):
        assert sut.is_dotfiles_repo("/home/user/myproject") is False


class TestMain:
    def make_input(self, command="git push origin main", cwd="/home/user/.dotfiles"):
        return json.dumps(
            {
                "tool_name": "Bash",
                "tool_input": {"command": command},
                "cwd": cwd,
            }
        )

    def test_passes_through_non_push_commands(self):
        with patch("sys.stdin", StringIO(self.make_input(command="git status"))):
            with pytest.raises(SystemExit) as exc:
                sut.main()
            assert exc.value.code == 0

    def test_passes_through_non_dotfiles_repo(self):
        repo_mock = MagicMock(returncode=0, stdout="/home/user/other-repo\n")
        with patch("subprocess.run", return_value=repo_mock):
            with patch(
                "sys.stdin",
                StringIO(self.make_input(cwd="/home/user/other-repo")),
            ):
                with pytest.raises(SystemExit) as exc:
                    sut.main()
                assert exc.value.code == 0

    def test_blocks_push_when_checks_fail(self, capsys):
        def mock_run(cmd, **kwargs):
            mock = MagicMock()
            if cmd[0] == "git":
                mock.returncode = 0
                mock.stdout = "/home/user/.dotfiles\n"
                return mock
            mock.returncode = 1
            mock.stdout = "error: unused variable\n"
            mock.stderr = ""
            return mock

        with patch("subprocess.run", side_effect=mock_run):
            with patch("sys.stdin", StringIO(self.make_input())):
                with pytest.raises(SystemExit) as exc:
                    sut.main()
                assert exc.value.code == 2
        captured = capsys.readouterr()
        assert "PUSH BLOCKED" in captured.err

    def test_allows_push_when_all_checks_pass(self):
        def mock_run(cmd, **kwargs):
            mock = MagicMock()
            if cmd[0] == "git":
                mock.returncode = 0
                mock.stdout = "/home/user/.dotfiles\n"
                return mock
            mock.returncode = 0
            mock.stdout = ""
            mock.stderr = ""
            return mock

        with patch("subprocess.run", side_effect=mock_run):
            with patch("sys.stdin", StringIO(self.make_input())):
                with pytest.raises(SystemExit) as exc:
                    sut.main()
                assert exc.value.code == 0

    def test_exits_cleanly_on_invalid_json(self):
        with patch("sys.stdin", StringIO("not json")):
            with pytest.raises(SystemExit) as exc:
                sut.main()
            assert exc.value.code == 1
