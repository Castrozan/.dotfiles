import json
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

import teammate_idle_quality_gate as sut


class TestGetStagedFileCount:
    def test_returns_zero_when_no_staged_files(self, tmp_path):
        mock_result = MagicMock(returncode=0, stdout="")
        with patch("subprocess.run", return_value=mock_result):
            assert sut.get_staged_file_count(str(tmp_path)) == 0

    def test_returns_count_of_staged_files(self, tmp_path):
        mock_result = MagicMock(returncode=0, stdout="file1.py\nfile2.nix\n")
        with patch("subprocess.run", return_value=mock_result):
            assert sut.get_staged_file_count(str(tmp_path)) == 2

    def test_returns_zero_when_git_fails(self, tmp_path):
        mock_result = MagicMock(returncode=128, stdout="")
        with patch("subprocess.run", return_value=mock_result):
            assert sut.get_staged_file_count(str(tmp_path)) == 0

    def test_ignores_blank_lines_in_git_output(self, tmp_path):
        mock_result = MagicMock(returncode=0, stdout="\nfile1.py\n\n")
        with patch("subprocess.run", return_value=mock_result):
            assert sut.get_staged_file_count(str(tmp_path)) == 1


class TestMain:
    def make_input(self, **kwargs):
        base = {
            "hook_event_name": "TeammateIdle",
            "cwd": "/tmp/test",
            "teammate_name": "researcher",
            "team_name": "my-team",
        }
        base.update(kwargs)
        return json.dumps(base)

    def test_exits_zero_when_no_staged_files(self):
        staged_mock = MagicMock(returncode=0, stdout="")
        with patch("subprocess.run", return_value=staged_mock):
            with patch("sys.stdin", StringIO(self.make_input())):
                with pytest.raises(SystemExit) as exc:
                    sut.main()
                assert exc.value.code == 0

    def test_exits_two_and_writes_stderr_when_staged_files_exist(self, capsys):
        staged_mock = MagicMock(returncode=0, stdout="foo.py\nbar.nix\n")
        with patch("subprocess.run", return_value=staged_mock):
            with patch("sys.stdin", StringIO(self.make_input())):
                with pytest.raises(SystemExit) as exc:
                    sut.main()
                assert exc.value.code == 2
        captured = capsys.readouterr()
        assert "2 staged file(s)" in captured.err
        assert "researcher" in captured.err

    def test_exits_zero_on_wrong_event(self):
        with patch("sys.stdin", StringIO(self.make_input(hook_event_name="PostToolUse"))):
            with pytest.raises(SystemExit) as exc:
                sut.main()
            assert exc.value.code == 0

    def test_exits_zero_on_invalid_json(self):
        with patch("sys.stdin", StringIO("not json")):
            with pytest.raises(SystemExit) as exc:
                sut.main()
            assert exc.value.code == 0

    def test_exits_zero_when_subprocess_raises(self):
        with patch("subprocess.run", side_effect=Exception("git not found")):
            with patch("sys.stdin", StringIO(self.make_input())):
                with pytest.raises(SystemExit) as exc:
                    sut.main()
                assert exc.value.code == 0
