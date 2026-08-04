"""The nix rebuild reminder speaks once per turn, and only when it is right.

The shape it replaced fired on every Edit of a .nix file and emitted the same
demand as both additional context and system message, so five edited files
produced five doubled copies. It fired at the one moment the demanded action
cannot be taken, and it never checked whether the obligation was outstanding,
so it also fired at an agent that had already committed and rebuilt.

This unit follows agents/hooks/lint/: a silent recorder appends to a
per-session ledger, and a Stop handler reads the ledger once and speaks only
if the work is genuinely unfinished, meaning the files are still uncommitted
or no system activation has happened since they were edited.
"""

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hook_module_loader import import_hyphenated_hook_module  # noqa: E402

nix_rebuild_ledger = import_hyphenated_hook_module("nix_rebuild_ledger")
nix_rebuild_obligation = import_hyphenated_hook_module("nix_rebuild_obligation")
record_changed_nix_file_handler = import_hyphenated_hook_module(
    "record_changed_nix_file_handler"
)
nix_rebuild_reminder_handler = import_hyphenated_hook_module(
    "nix_rebuild_reminder_handler"
)


def clear_session_ledger(session_id):
    try:
        os.remove(nix_rebuild_ledger.ledger_file_path_for_session(session_id))
    except OSError:
        pass


def make_dotfiles_repository(root):
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "t"], check=True)
    marker_directory = root / "agents" / "hooks" / "nix-rebuild"
    marker_directory.mkdir(parents=True)
    marker_directory.joinpath("nix_rebuild_obligation.py").write_text("")
    return root


def commit_paths(root, paths):
    subprocess.run(
        ["git", "-C", str(root), "add", "--", *(str(path) for path in paths)],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(root), "commit", "--no-verify", "-qm", "fix(test): fixture"],
        check=True,
    )


def record_edit_of(session_id, nix_file):
    return record_changed_nix_file_handler.handle(
        {
            "session_id": session_id,
            "tool_name": "Edit",
            "tool_input": {"file_path": str(nix_file)},
        }
    )


def stop_the_turn(session_id, stop_hook_active=False):
    return nix_rebuild_reminder_handler.handle(
        {
            "session_id": session_id,
            "hook_event_name": "Stop",
            "stop_hook_active": stop_hook_active,
        }
    )


def pretend_activation_happened(monkeypatch, nix_file, offset_seconds):
    edited_at = nix_rebuild_obligation.newest_modification_time([str(nix_file)])
    monkeypatch.setattr(
        nix_rebuild_obligation,
        "last_system_activation_time",
        lambda: edited_at + offset_seconds,
    )


def test_the_recorder_stays_silent_and_only_writes_the_ledger(tmp_path):
    session_id = "pytest-nix-rebuild-recorder"
    clear_session_ledger(session_id)
    repository = make_dotfiles_repository(tmp_path / "repo")
    nix_file = repository / "flake.nix"
    nix_file.write_text("{}")

    assert record_edit_of(session_id, nix_file) is None, (
        "the recorder speaks at Stop through the ledger, not at edit time"
    )
    assert nix_rebuild_ledger.read_and_clear_changed_nix_files(session_id) == [
        str(nix_file)
    ]


def test_editing_five_nix_files_produces_one_reminder(tmp_path):
    session_id = "pytest-nix-rebuild-five-files"
    clear_session_ledger(session_id)
    repository = make_dotfiles_repository(tmp_path / "repo")
    for index in range(5):
        nix_file = repository / f"module{index}.nix"
        nix_file.write_text("{}")
        record_edit_of(session_id, nix_file)

    result = stop_the_turn(session_id)

    assert result is not None
    assert result.decision == "block"
    assert result.reason.count("uncommitted") == 1, (
        "one turn earns one reminder, however many nix files it touched"
    )
    for index in range(5):
        assert f"module{index}.nix" in result.reason


def test_the_reminder_stays_quiet_once_the_files_are_committed_and_activated(
    tmp_path, monkeypatch
):
    session_id = "pytest-nix-rebuild-finished"
    clear_session_ledger(session_id)
    repository = make_dotfiles_repository(tmp_path / "repo")
    nix_file = repository / "flake.nix"
    nix_file.write_text("{}")
    record_edit_of(session_id, nix_file)
    commit_paths(repository, [nix_file])
    pretend_activation_happened(monkeypatch, nix_file, offset_seconds=1)

    assert stop_the_turn(session_id) is None, (
        "committed and activated is the finished state the old handler still nagged at"
    )


def test_a_committed_but_unactivated_change_still_asks_for_the_rebuild(
    tmp_path, monkeypatch
):
    session_id = "pytest-nix-rebuild-unactivated"
    clear_session_ledger(session_id)
    repository = make_dotfiles_repository(tmp_path / "repo")
    nix_file = repository / "flake.nix"
    nix_file.write_text("{}")
    record_edit_of(session_id, nix_file)
    commit_paths(repository, [nix_file])
    pretend_activation_happened(monkeypatch, nix_file, offset_seconds=-1)

    result = stop_the_turn(session_id)

    assert result.decision == "block"
    assert "not activated" in result.reason


def test_a_nix_file_outside_the_dotfiles_repository_is_never_recorded(tmp_path):
    session_id = "pytest-nix-rebuild-foreign-repo"
    clear_session_ledger(session_id)
    foreign_nix_file = tmp_path / "someone-elses-project" / "flake.nix"
    foreign_nix_file.parent.mkdir(parents=True)
    foreign_nix_file.write_text("{}")

    record_edit_of(session_id, foreign_nix_file)

    assert nix_rebuild_ledger.read_and_clear_changed_nix_files(session_id) == []


def test_a_reentered_stop_hook_does_not_block_again(tmp_path):
    session_id = "pytest-nix-rebuild-reentered"
    clear_session_ledger(session_id)
    repository = make_dotfiles_repository(tmp_path / "repo")
    nix_file = repository / "flake.nix"
    nix_file.write_text("{}")
    record_edit_of(session_id, nix_file)

    assert stop_the_turn(session_id, stop_hook_active=True) is None, (
        "a blocking Stop handler that ignores stop_hook_active traps the turn"
    )


def test_a_turn_that_touched_no_nix_file_says_nothing():
    session_id = "pytest-nix-rebuild-quiet-turn"
    clear_session_ledger(session_id)

    assert stop_the_turn(session_id) is None
