import json
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import task_completed_quality_gate as sut


class TestGetRecentlyModifiedFiles:
    def test_returns_empty_when_no_changes(self, tmp_path):
        mock_result = MagicMock(returncode=0, stdout="")
        with patch("subprocess.run", return_value=mock_result):
            assert sut.get_recently_modified_files(str(tmp_path)) == []

    def test_returns_list_of_modified_files(self, tmp_path):
        mock_result = MagicMock(returncode=0, stdout="foo.py\nbar.nix\n")
        with patch("subprocess.run", return_value=mock_result):
            assert sut.get_recently_modified_files(str(tmp_path)) == ["foo.py", "bar.nix"]

    def test_returns_empty_when_git_fails(self, tmp_path):
        mock_result = MagicMock(returncode=128, stdout="")
        with patch("subprocess.run", return_value=mock_result):
            assert sut.get_recently_modified_files(str(tmp_path)) == []


class TestRunFormatCheck:
    def test_returns_empty_when_no_relevant_files(self, tmp_path):
        failures = sut.run_format_check(str(tmp_path), ["readme.md", "image.png"])
        assert failures == []

    def test_nix_file_passes_when_nixfmt_exits_zero(self, tmp_path):
        nix_file = tmp_path / "config.nix"
        nix_file.write_text("{ }")
        mock_result = MagicMock(returncode=0, stdout="")
        with patch("subprocess.run", return_value=mock_result):
            failures = sut.run_format_check(str(tmp_path), ["config.nix"])
        assert failures == []

    def test_nix_file_fails_when_nixfmt_exits_nonzero(self, tmp_path):
        nix_file = tmp_path / "config.nix"
        nix_file.write_text("{}")
        mock_result = MagicMock(returncode=1, stdout="")
        with patch("subprocess.run", return_value=mock_result):
            failures = sut.run_format_check(str(tmp_path), ["config.nix"])
        assert len(failures) == 1
        assert "nixfmt" in failures[0]
        assert "config.nix" in failures[0]

    def test_python_file_fails_when_ruff_exits_nonzero(self, tmp_path):
        py_file = tmp_path / "script.py"
        py_file.write_text("x=1")
        mock_result = MagicMock(returncode=1, stdout="E501 line too long")
        with patch("subprocess.run", return_value=mock_result):
            failures = sut.run_format_check(str(tmp_path), ["script.py"])
        assert len(failures) == 1
        assert "ruff" in failures[0]

    def test_shell_file_fails_when_shellcheck_exits_nonzero(self, tmp_path):
        sh_file = tmp_path / "run.sh"
        sh_file.write_text("#!/bin/bash\nfoo")
        mock_result = MagicMock(returncode=1, stdout="SC2034: foo unused")
        with patch("subprocess.run", return_value=mock_result):
            failures = sut.run_format_check(str(tmp_path), ["run.sh"])
        assert len(failures) == 1
        assert "shellcheck" in failures[0]

    def test_skips_nix_file_that_does_not_exist(self, tmp_path):
        failures = sut.run_format_check(str(tmp_path), ["missing.nix"])
        assert failures == []

    def test_multiple_file_types_checked(self, tmp_path):
        (tmp_path / "a.nix").write_text("{ }")
        (tmp_path / "b.py").write_text("x=1")
        nix_pass = MagicMock(returncode=0, stdout="")
        ruff_fail = MagicMock(returncode=1, stdout="E501")
        with patch("subprocess.run", side_effect=[nix_pass, ruff_fail]):
            failures = sut.run_format_check(str(tmp_path), ["a.nix", "b.py"])
        assert len(failures) == 1
        assert "ruff" in failures[0]


class TestMain:
    def make_input(self, **kwargs):
        base = {
            "hook_event_name": "TaskCompleted",
            "cwd": "/tmp/test",
            "task_id": "task-001",
            "task_subject": "Add login endpoint",
            "task_description": "Implement POST /login",
            "teammate_name": "implementer",
            "team_name": "my-team",
        }
        base.update(kwargs)
        return json.dumps(base)

    def test_exits_zero_when_no_modified_files(self, tmp_path):
        git_mock = MagicMock(returncode=0, stdout="")
        with patch("subprocess.run", return_value=git_mock):
            with patch("sys.stdin", StringIO(self.make_input(cwd=str(tmp_path)))):
                with pytest.raises(SystemExit) as exc:
                    sut.main()
                assert exc.value.code == 0

    def test_exits_zero_when_all_format_checks_pass(self, tmp_path):
        (tmp_path / "config.nix").write_text("{ }")
        git_mock = MagicMock(returncode=0, stdout="config.nix\n")
        nixfmt_mock = MagicMock(returncode=0, stdout="")
        with patch("subprocess.run", side_effect=[git_mock, nixfmt_mock]):
            with patch("sys.stdin", StringIO(self.make_input(cwd=str(tmp_path)))):
                with pytest.raises(SystemExit) as exc:
                    sut.main()
                assert exc.value.code == 0

    def test_exits_two_and_writes_stderr_when_format_check_fails(self, tmp_path, capsys):
        (tmp_path / "config.nix").write_text("{}")
        git_mock = MagicMock(returncode=0, stdout="config.nix\n")
        nixfmt_fail = MagicMock(returncode=1, stdout="")
        with patch("subprocess.run", side_effect=[git_mock, nixfmt_fail]):
            with patch("sys.stdin", StringIO(self.make_input(cwd=str(tmp_path)))):
                with pytest.raises(SystemExit) as exc:
                    sut.main()
                assert exc.value.code == 2
        captured = capsys.readouterr()
        assert "nixfmt" in captured.err
        assert "Add login endpoint" in captured.err

    def test_exits_zero_on_wrong_event(self):
        with patch("sys.stdin", StringIO(self.make_input(hook_event_name="TeammateIdle"))):
            with pytest.raises(SystemExit) as exc:
                sut.main()
            assert exc.value.code == 0

    def test_exits_zero_on_invalid_json(self):
        with patch("sys.stdin", StringIO("not json")):
            with pytest.raises(SystemExit) as exc:
                sut.main()
            assert exc.value.code == 0

    def test_exits_zero_when_subprocess_raises(self, tmp_path):
        with patch("subprocess.run", side_effect=Exception("git not found")):
            with patch("sys.stdin", StringIO(self.make_input(cwd=str(tmp_path)))):
                with pytest.raises(SystemExit) as exc:
                    sut.main()
                assert exc.value.code == 0
