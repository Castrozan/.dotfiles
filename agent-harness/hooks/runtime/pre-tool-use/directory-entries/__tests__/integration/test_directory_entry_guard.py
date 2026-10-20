import subprocess

import pytest

from directory_entry_guard_handler import handle
from hook_dispatch import EVERY_SURFACE, HookHandler, run_handlers


@pytest.fixture
def crowded_repository(repository_at_entry_limit):
    (repository_at_entry_limit / "source/file15.py").touch()
    return repository_at_entry_limit


def fail_if_called(*arguments):
    raise AssertionError("This tool call must not enumerate the repository")


@pytest.mark.parametrize("surface", EVERY_SURFACE)
def test_all_harness_surfaces_deny_creating_sixteenth_entry(
    repository_at_entry_limit, surface
):
    result = run_handlers(
        {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(repository_at_entry_limit / "source/file15.py")
            },
        },
        [HookHandler(handle=handle, tool_matcher="Edit|Write")],
        surface,
    )
    assert result.decision == "deny"
    assert "source has 16 immediate files/folders combined (limit 15)" in result.reason


def test_patch_nested_creation_denies_growth_of_existing_ancestor(
    repository_at_entry_limit,
):
    result = handle(
        {
            "tool_name": "apply_patch",
            "cwd": str(repository_at_entry_limit),
            "tool_input": "*** Add File: source/module/file.py\n+pass\n",
        }
    )
    assert result.decision == "deny"
    assert "source has 16" in result.reason


def test_patch_update_of_existing_file_in_crowded_directory_is_allowed(
    crowded_repository, monkeypatch
):
    monkeypatch.setattr(
        "repository_directory_entries.repository_root_for_path", fail_if_called
    )
    assert (
        handle(
            {
                "tool_name": "apply_patch",
                "cwd": str(crowded_repository),
                "tool_input": "*** Update File: source/file15.py\n+pass\n",
            }
        )
        is None
    )


def test_symlinked_repository_path_cannot_bypass_limit(
    repository_at_entry_limit, tmp_path
):
    alias = tmp_path / "alias"
    alias.symlink_to(repository_at_entry_limit, target_is_directory=True)
    result = handle(
        {
            "tool_name": "Write",
            "tool_input": {"file_path": str(alias / "source/file15.py")},
        }
    )
    assert result.decision == "deny"


@pytest.mark.parametrize("tool_name", ["Edit", "Write"])
def test_existing_file_in_crowded_directory_does_not_enumerate(
    crowded_repository, monkeypatch, tool_name
):
    monkeypatch.setattr(
        "repository_directory_entries.repository_root_for_path", fail_if_called
    )
    target = crowded_repository / "source/file15.py"
    assert (
        handle({"tool_name": tool_name, "tool_input": {"file_path": str(target)}})
        is None
    )


def test_creation_inside_existing_module_of_crowded_directory_is_allowed(
    crowded_repository,
):
    module = crowded_repository / "source/module"
    module.mkdir()
    (module / "existing.py").touch()
    assert (
        handle(
            {
                "tool_name": "Write",
                "tool_input": {"file_path": str(module / "new.py")},
            }
        )
        is None
    )


def test_creation_outside_crowded_directory_is_allowed(crowded_repository):
    target = crowded_repository / "other.py"
    assert (
        handle({"tool_name": "Write", "tool_input": {"file_path": str(target)}}) is None
    )


def test_creation_reaching_the_limit_is_allowed(repository_at_entry_limit):
    (repository_at_entry_limit / "source/file14.py").unlink()
    target = repository_at_entry_limit / "source/file15.py"
    assert (
        handle({"tool_name": "Write", "tool_input": {"file_path": str(target)}}) is None
    )


def test_read_does_not_enumerate_repository(repository_at_entry_limit, monkeypatch):
    monkeypatch.setattr(
        "repository_directory_entries.repository_root_for_path", fail_if_called
    )
    assert (
        handle(
            {
                "tool_name": "Read",
                "tool_input": {
                    "file_path": str(repository_at_entry_limit / "source/file15.py")
                },
            }
        )
        is None
    )


def test_git_timeout_denies_with_actionable_failure(
    repository_at_entry_limit, monkeypatch
):
    def time_out(*arguments):
        raise subprocess.TimeoutExpired("git", 5)

    monkeypatch.setattr("repository_directory_entries.repository_entry_paths", time_out)
    result = handle(
        {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(repository_at_entry_limit / "source/file15.py")
            },
        }
    )
    assert result.decision == "deny"
    assert "could not complete" in result.reason


def test_creation_outside_repository_does_not_enumerate(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "repository_directory_entries.repository_root_for_path", fail_if_called
    )
    target = tmp_path / "note.md"
    assert (
        handle({"tool_name": "Write", "tool_input": {"file_path": str(target)}}) is None
    )
