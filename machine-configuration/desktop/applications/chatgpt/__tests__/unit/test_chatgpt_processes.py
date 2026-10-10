from pathlib import Path

import pytest

import chatgpt_processes as processes
from chatgpt_processes import ProcessIdentity


@pytest.fixture
def process_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(
        processes, "Path", lambda value: tmp_path if value == "/proc" else Path(value)
    )
    fields = ["0"] * 22
    fields[19] = "100"
    root = tmp_path / "42"
    root.mkdir()
    (root / "stat").write_text("42 (ChatGPT) " + " ".join(fields))
    (root / "cgroup").write_text("0::/app-chatgpt-test.scope\n")
    (root / "cmdline").write_bytes(b"ChatGPT\0")
    (root / "exe").symlink_to("/vendor/lib/chatgpt/ChatGPT")
    return root


def test_process_identity_and_group_are_read_from_kernel_files(process_directory):
    assert ProcessIdentity.read(42) == ProcessIdentity(42, 100)
    assert processes.process_cgroup(42) == "/app-chatgpt-test.scope"
    assert processes.is_primary_chatgpt_process(ProcessIdentity(42, 100))


def test_missing_process_cannot_be_identified_or_attached(process_directory):
    assert ProcessIdentity.read(99) is None
    assert processes.process_cgroup(99) is None
    assert not processes.is_primary_chatgpt_process(ProcessIdentity(99, 100))


def test_malformed_kernel_identity_and_group_are_unknown(process_directory):
    (process_directory / "stat").write_text("invalid")
    (process_directory / "cgroup").write_text("invalid")
    assert ProcessIdentity.read(42) is None
    assert processes.process_cgroup(42) is None


def test_renderer_is_excluded_from_main_process_detection(process_directory):
    (process_directory / "cmdline").write_bytes(b"ChatGPT --type=renderer\0")
    assert not processes.is_primary_chatgpt_process(ProcessIdentity(42, 100))


def test_process_walk_handles_cycles_and_disappearing_children(process_directory):
    thread = process_directory / "task" / "42"
    thread.mkdir(parents=True)
    (thread / "children").write_text("42 99")
    assert processes.process_tree(42) == {ProcessIdentity(42, 100)}
    assert processes.process_children(99) == []


def test_unreadable_or_malformed_children_do_not_escape_process_walk(process_directory):
    thread = process_directory / "task" / "42"
    thread.mkdir(parents=True)
    assert processes.thread_children(thread) == []
    (thread / "children").write_text("invalid")
    assert processes.thread_children(thread) == []
