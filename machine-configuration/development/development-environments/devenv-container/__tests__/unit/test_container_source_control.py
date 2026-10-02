from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from container_source_control import shared_git_metadata


def test_mount_shared_worktree_metadata_without_exposing_other_source_checkouts(
    tmp_path,
):
    project_directory = tmp_path / "repo" / "worktree"
    project_directory.mkdir(parents=True)
    (project_directory / ".git").write_text("gitdir: ../main/.git/worktrees/worktree")
    metadata = tmp_path / "repo" / "main" / ".git"
    command = Mock(return_value=SimpleNamespace(stdout=str(metadata)))
    result = shared_git_metadata(
        SimpleNamespace(directory=project_directory), tmp_path / "repo", command
    )
    assert result == [metadata]
    assert command.call_args.args[0][-1] == "--git-common-dir"


def test_reject_metadata_that_would_escape_the_workspace_root(tmp_path):
    project_directory = tmp_path / "repo" / "worktree"
    project_directory.mkdir(parents=True)
    (project_directory / ".git").write_text("gitdir: /outside")
    command = Mock(return_value=SimpleNamespace(stdout=str(tmp_path / "outside")))
    with pytest.raises(ValueError, match="inside"):
        shared_git_metadata(
            SimpleNamespace(directory=project_directory), tmp_path / "repo", command
        )


def test_normal_checkout_already_contains_its_git_metadata(tmp_path):
    (tmp_path / ".git").mkdir()
    command = Mock()
    assert (
        shared_git_metadata(
            SimpleNamespace(directory=Path(tmp_path)), tmp_path, command
        )
        == []
    )
    command.assert_not_called()
