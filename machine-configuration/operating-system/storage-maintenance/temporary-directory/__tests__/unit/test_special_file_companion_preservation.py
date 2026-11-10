import contextlib
import os
import socket
import stat
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from temporary_directory_cleanup_run import remove_everything_written_before_now


def create_named_pipe(path: Path) -> None:
    os.mkfifo(path)


def create_unix_socket(path: Path) -> None:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as unix_socket:
        unix_socket.bind(path.name)


def create_regular_file(path: Path) -> None:
    path.write_text("12345")


def create_symlink_to_existing_file(path: Path) -> None:
    link_target = path.with_name(f"{path.name}-target")
    link_target.write_text("target")
    path.symlink_to(link_target)


def create_dangling_symlink(path: Path) -> None:
    path.symlink_to("4141210184314747129")


SPECIAL_FILE_CREATORS = [create_named_pipe, create_unix_socket]
REMOVABLE_FILE_CREATORS = [
    create_regular_file,
    create_symlink_to_existing_file,
    create_dangling_symlink,
]


@pytest.mark.parametrize("create_special_file", SPECIAL_FILE_CREATORS)
def test_never_removes_special_files_or_the_directory_holding_them(
    tmp_path, monkeypatch, create_special_file
):
    channel_directory = tmp_path / "agent-channel"
    channel_directory.mkdir()
    monkeypatch.chdir(channel_directory)
    special_file = channel_directory / "endpoint"
    create_special_file(special_file)

    result = remove_everything_written_before_now(tmp_path)

    special_file_mode = os.lstat(special_file).st_mode
    assert stat.S_ISFIFO(special_file_mode) or stat.S_ISSOCK(special_file_mode)
    assert result.failed_entry_count == 0


@settings(deadline=None, max_examples=30)
@given(
    create_special_file=st.sampled_from(SPECIAL_FILE_CREATORS),
    create_companions=st.lists(
        st.sampled_from(REMOVABLE_FILE_CREATORS), min_size=1, max_size=4
    ),
)
def test_keeps_every_stale_file_directly_beside_a_special_file(
    create_special_file, create_companions
):
    with tempfile.TemporaryDirectory() as temporary_root:
        singleton_directory = Path(temporary_root) / "browser-singleton"
        singleton_directory.mkdir()
        with contextlib.chdir(singleton_directory):
            create_special_file(singleton_directory / "endpoint")
        companions = [
            singleton_directory / f"companion-{index}"
            for index in range(len(create_companions))
        ]
        for create_companion, companion in zip(
            create_companions, companions, strict=True
        ):
            create_companion(companion)

        result = remove_everything_written_before_now(Path(temporary_root))

        assert all(os.path.lexists(companion) for companion in companions)
        assert result.removed_entry_count == 0
        assert result.failed_entry_count == 0


@pytest.mark.parametrize("create_special_file", SPECIAL_FILE_CREATORS)
def test_still_ages_out_a_stale_directory_beside_a_special_file(
    tmp_path, monkeypatch, create_special_file
):
    automation_profile = tmp_path / "automation-profile"
    stale_cache = automation_profile / "cache"
    stale_cache.mkdir(parents=True)
    (stale_cache / "blob").write_text("cached")
    monkeypatch.chdir(automation_profile)
    create_special_file(automation_profile / "endpoint")

    result = remove_everything_written_before_now(tmp_path)

    assert not stale_cache.exists()
    assert os.path.lexists(automation_profile / "endpoint")
    assert result.failed_entry_count == 0
