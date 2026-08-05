import importlib.util
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[2]
CHANGED_FILE_PATHS_SOURCE = HOOKS_ROOT / "common" / "changed_file_paths.py"

_spec = importlib.util.spec_from_file_location(
    "changed_file_paths", CHANGED_FILE_PATHS_SOURCE
)
changed_file_paths = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(changed_file_paths)

collect_changed_file_paths = changed_file_paths.collect_changed_file_paths


def test_claude_edit_shape_returns_direct_file_path(tmp_path):
    edited_file = tmp_path / "module.nix"
    payload = {"tool_name": "Edit", "tool_input": {"file_path": str(edited_file)}}
    assert collect_changed_file_paths(payload) == [str(edited_file)]


def test_codex_apply_patch_update_marker_resolves_against_cwd(tmp_path):
    patch = (
        "*** Begin Patch\n"
        "*** Update File: home/base/codex/config.nix\n"
        "@@\n-a\n+b\n"
        "*** End Patch"
    )
    payload = {
        "tool_name": "shell",
        "cwd": str(tmp_path),
        "tool_input": {"command": ["apply_patch", patch]},
    }
    expected = str(tmp_path / "home" / "base" / "codex" / "config.nix")
    assert collect_changed_file_paths(payload) == [expected]


def test_codex_apply_patch_json_escaped_newlines(tmp_path):
    payload = {
        "cwd": str(tmp_path),
        "tool_input": "*** Begin Patch\\n*** Add File: pkg/new_module.py\\n*** End Patch",
    }
    expected = str(tmp_path / "pkg" / "new_module.py")
    assert collect_changed_file_paths(payload) == [expected]


def test_codex_apply_patch_multiple_files_deduplicated_in_order(tmp_path):
    patch = (
        "*** Begin Patch\n"
        "*** Update File: a.nix\n"
        "*** Add File: b.py\n"
        "*** Update File: a.nix\n"
        "*** End Patch"
    )
    payload = {"cwd": str(tmp_path), "tool_input": {"input": patch}}
    assert collect_changed_file_paths(payload) == [
        str(tmp_path / "a.nix"),
        str(tmp_path / "b.py"),
    ]


def test_codex_apply_patch_delete_marker(tmp_path):
    patch = "*** Begin Patch\n*** Delete File: old/legacy.nix\n*** End Patch"
    payload = {"cwd": str(tmp_path), "tool_input": {"command": ["apply_patch", patch]}}
    assert collect_changed_file_paths(payload) == [str(tmp_path / "old" / "legacy.nix")]


def test_codex_apply_patch_move_marker_reports_source_and_destination(tmp_path):
    patch = (
        "*** Begin Patch\n"
        "*** Update File: src/a.py\n"
        "*** Move to: src/b.py\n"
        "*** End Patch"
    )
    payload = {"cwd": str(tmp_path), "tool_input": {"command": ["apply_patch", patch]}}
    assert collect_changed_file_paths(payload) == [
        str(tmp_path / "src" / "a.py"),
        str(tmp_path / "src" / "b.py"),
    ]


def test_marker_text_in_tool_response_is_ignored(tmp_path):
    payload = {
        "tool_name": "shell",
        "cwd": str(tmp_path),
        "tool_input": {"command": ["cat", "notes.md"]},
        "tool_response": "*** Begin Patch\n*** Update File: unrelated.nix\n*** End Patch",
    }
    assert collect_changed_file_paths(payload) == []


def test_marker_like_text_inside_patch_body_is_not_captured(tmp_path):
    patch = (
        "*** Begin Patch\n"
        "*** Update File: real.nix\n"
        "@@\n"
        "+*** Update File: fake.nix\n"
        "*** End Patch"
    )
    payload = {"cwd": str(tmp_path), "tool_input": {"command": ["apply_patch", patch]}}
    assert collect_changed_file_paths(payload) == [str(tmp_path / "real.nix")]


def test_absolute_marker_path_is_preserved(tmp_path):
    absolute_target = tmp_path / "abs.nix"
    patch = f"*** Begin Patch\n*** Update File: {absolute_target}\n*** End Patch"
    payload = {"cwd": "/some/other/dir", "tool_input": {"input": patch}}
    assert collect_changed_file_paths(payload) == [str(absolute_target)]


def test_no_edit_payload_returns_empty():
    assert collect_changed_file_paths({"tool_name": "shell", "tool_input": {}}) == []
