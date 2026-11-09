import subprocess

import pytest

from workspaces import (
    is_inside_git_checkout,
    resolve_repository_root,
    workspace_arguments,
)


@pytest.fixture
def checkout(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, timeout=30)
    (tmp_path / "nested").mkdir()
    return tmp_path


def test_a_git_checkout_runs_in_place_through_its_path(checkout):
    assert is_inside_git_checkout(checkout / "nested")
    assert workspace_arguments(checkout, True) == ["--cwd", str(checkout)]


def test_a_plain_directory_runs_as_a_folder_project(tmp_path):
    assert not is_inside_git_checkout(tmp_path)
    assert workspace_arguments(tmp_path, False) == ["--folder"]


def test_the_root_defaults_to_the_checkout_holding_the_current_directory(
    checkout, monkeypatch
):
    monkeypatch.chdir(checkout / "nested")
    assert resolve_repository_root("") == checkout.resolve()


def test_an_explicit_root_must_be_a_directory(tmp_path):
    with pytest.raises(SystemExit, match="is not a directory"):
        resolve_repository_root(str(tmp_path / "missing"))


def test_outside_any_checkout_the_root_must_be_passed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit, match="pass --root"):
        resolve_repository_root("")
