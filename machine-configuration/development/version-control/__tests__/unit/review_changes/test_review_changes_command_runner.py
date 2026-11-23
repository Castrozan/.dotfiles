from unittest.mock import MagicMock, patch

import pytest

import review_command_runner


def test_failed_git_command_raises_with_its_stderr():
    failed = MagicMock(returncode=128, stdout="", stderr="fatal: bad revision\n")
    with (
        patch("review_command_runner.subprocess.run", return_value=failed),
        pytest.raises(
            review_command_runner.ReviewTargetError, match="fatal: bad revision"
        ),
    ):
        review_command_runner.run_git(["rev-parse", "missing"])
