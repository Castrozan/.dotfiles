import subprocess
from unittest.mock import MagicMock, patch

import pytest

import command_runner


def test_helpers_never_read_the_review_terminal_which_may_already_be_gone():
    with patch(
        "command_runner.subprocess.run", return_value=MagicMock(returncode=0)
    ) as run:
        command_runner.run_command(["herdr", "pane", "close", "w1:p2"])
    assert run.call_args.kwargs["stdin"] is subprocess.DEVNULL


def test_failed_git_command_raises_with_its_stderr():
    failed = MagicMock(returncode=128, stdout="", stderr="fatal: bad revision\n")
    with (
        patch("command_runner.subprocess.run", return_value=failed),
        pytest.raises(command_runner.ReviewTargetError, match="fatal: bad revision"),
    ):
        command_runner.run_git(["rev-parse", "missing"])
