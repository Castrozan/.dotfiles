import os
import socket
import stat
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import temporary_directory_cleanup
from temporary_directory_cleanup import CleanupPolicy, CleanupResult, StaleEntryRemover

FRESHNESS_MARGIN_SECONDS = 3600
TIMESTAMP_ORDERING_PAUSE_SECONDS = 0.01
AGENIX_TOP_LEVEL_NAMES = frozenset({"agenix", "agenix.d"})


def policy_treating_existing_entries_as_stale(
    temporary_directory: Path,
) -> CleanupPolicy:
    time.sleep(TIMESTAMP_ORDERING_PAUSE_SECONDS)
    stale_before_timestamp = time.time()
    time.sleep(TIMESTAMP_ORDERING_PAUSE_SECONDS)
    return CleanupPolicy(
        temporary_directory, stale_before_timestamp, AGENIX_TOP_LEVEL_NAMES
    )


def remove_everything_written_before_now(temporary_directory: Path) -> CleanupResult:
    policy = policy_treating_existing_entries_as_stale(temporary_directory)
    return StaleEntryRemover(policy).remove_stale_top_level_entries()


def mark_fresh(path: Path) -> None:
    future_timestamp = time.time() + FRESHNESS_MARGIN_SECONDS
    os.utime(path, (future_timestamp, future_timestamp), follow_symlinks=False)


def create_named_pipe(path: Path) -> None:
    os.mkfifo(path)


def create_unix_socket(path: Path) -> None:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as unix_socket:
        unix_socket.bind(path.name)


def test_removes_a_deep_stale_tree_in_one_run(tmp_path):
    deepest_directory = tmp_path / "leaked-fixture" / "nested" / "deeper"
    deepest_directory.mkdir(parents=True)
    (deepest_directory / "result.txt").write_text("leaked")

    result = remove_everything_written_before_now(tmp_path)

    assert list(tmp_path.iterdir()) == []
    assert result.removed_entry_count == 4


def test_keeps_a_fresh_file_and_its_ancestors_while_removing_stale_siblings(tmp_path):
    active_run = tmp_path / "pytest-of-user" / "pytest-3"
    abandoned_run = tmp_path / "pytest-of-user" / "garbage-1234"
    active_run.mkdir(parents=True)
    abandoned_run.mkdir()
    (abandoned_run / "leftover.txt").write_text("leftover")
    current_file = active_run / "current.txt"
    current_file.write_text("current")
    mark_fresh(current_file)

    remove_everything_written_before_now(tmp_path)

    assert current_file.exists()
    assert not abandoned_run.exists()


def test_keeps_a_fresh_directory_after_removing_its_stale_children(tmp_path):
    active_directory = tmp_path / "active-session"
    active_directory.mkdir()
    (active_directory / "old.txt").write_text("old")
    mark_fresh(active_directory)

    remove_everything_written_before_now(tmp_path)

    assert active_directory.is_dir()
    assert list(active_directory.iterdir()) == []


@pytest.mark.parametrize("create_special_file", [create_named_pipe, create_unix_socket])
def test_never_removes_special_files_or_the_directory_holding_them(
    tmp_path, monkeypatch, create_special_file
):
    channel_directory = tmp_path / "agent-channel"
    channel_directory.mkdir()
    monkeypatch.chdir(channel_directory)
    special_file = channel_directory / "endpoint"
    create_special_file(special_file)

    remove_everything_written_before_now(tmp_path)

    special_file_mode = os.lstat(special_file).st_mode
    assert stat.S_ISFIFO(special_file_mode) or stat.S_ISSOCK(special_file_mode)


@pytest.mark.parametrize(
    "top_level_name", ["agenix", "agenix.d", "com.apple.chrono", ".AddressBookLocks"]
)
def test_leaves_protected_top_level_entries_untouched(tmp_path, top_level_name):
    protected_directory = tmp_path / top_level_name / "1"
    protected_directory.mkdir(parents=True)
    (protected_directory / "secret").write_text("secret")

    remove_everything_written_before_now(tmp_path)

    assert (protected_directory / "secret").exists()


def test_removes_a_stale_symlink_without_touching_its_target(tmp_path):
    temporary_directory = tmp_path / "T"
    temporary_directory.mkdir()
    link_target = tmp_path / "target.txt"
    link_target.write_text("target")
    (temporary_directory / "link").symlink_to(link_target)

    remove_everything_written_before_now(temporary_directory)

    assert list(temporary_directory.iterdir()) == []
    assert link_target.read_text() == "target"


def test_removes_stale_entries_inside_an_owner_read_only_directory(tmp_path):
    store_copy = tmp_path / "nix-store-copy"
    store_copy.mkdir()
    (store_copy / "file.txt").write_text("copied")
    store_copy.chmod(0o555)

    result = remove_everything_written_before_now(tmp_path)

    assert not store_copy.exists()
    assert result.failed_entry_count == 0


def test_does_not_descend_into_another_device(tmp_path):
    (tmp_path / "mounted-image").mkdir()
    remover = StaleEntryRemover(policy_treating_existing_entries_as_stale(tmp_path))
    remover.root_device = -1

    remover.remove_stale_top_level_entries()

    assert (tmp_path / "mounted-image").is_dir()


@pytest.mark.parametrize(
    "reported_directory", ["/tmp/", "/Users/user/", "/var/folders/ab/cd/C/"]
)
def test_refuses_a_temporary_directory_outside_per_user_var_folders(reported_directory):
    with patch("temporary_directory_cleanup.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=f"{reported_directory}\n")
        with pytest.raises(ValueError, match="refusing to clean"):
            temporary_directory_cleanup.resolve_per_user_temporary_directory()


def test_accepts_the_per_user_var_folders_temporary_directory():
    reported_directory = "/var/folders/8s/fg53rbc55953s5rsg4xr45pw0000gp/T/"
    with patch("temporary_directory_cleanup.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=f"{reported_directory}\n")
        assert (
            temporary_directory_cleanup.resolve_per_user_temporary_directory()
            == Path(reported_directory)
        )
