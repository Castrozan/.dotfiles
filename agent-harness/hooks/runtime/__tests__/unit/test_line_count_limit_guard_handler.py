import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hook_module_loader import import_hyphenated_hook_module

line_count_limit_guard_handler = import_hyphenated_hook_module(
    "line_count_limit_guard_handler"
)


def write_python_file_with_line_count(
    parent_directory: Path, file_basename: str, line_count: int
) -> Path:
    file_path = parent_directory / file_basename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("\n".join(f"line_{n}" for n in range(line_count)) + "\n")
    return file_path


def record_line_counts(repository_root: Path, baseline_text: str) -> Path:
    baseline_path = (
        repository_root / "repository" / "verification" / "line-count-baseline.json"
    )
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_path.write_text(baseline_text)
    return repository_root


def handle_edit_of(file_path: Path):
    return line_count_limit_guard_handler.handle(
        {"tool_name": "Edit", "tool_input": {"file_path": str(file_path)}}
    )


def test_blocks_edit_of_code_file_over_threshold(tmp_path):
    file_path = write_python_file_with_line_count(tmp_path, "over.py", 250)
    result = handle_edit_of(file_path)
    assert result is not None
    assert result.decision == "block"
    assert "250" in result.reason
    assert "BLOCKED" in result.system_message


def test_the_block_states_what_is_blocked_and_points_at_the_detail(tmp_path):
    file_path = write_python_file_with_line_count(tmp_path, "over.py", 250)
    result = handle_edit_of(file_path)
    assert "line-count-block-message.md" in result.reason, (
        "a deny reason names what is blocked and points at the file carrying the "
        "rest, the way the streaming-pattern guard points at its reference file; "
        "the agent reads it when it needs the detail"
    )
    reason_without_the_file_path = result.reason.replace(str(file_path), "")
    assert len(reason_without_the_file_path) <= 240, (
        "inlining the whole guidance turns one blocked write into a wall covering "
        "the split rule, the domain-subfolder rule and the nix directory-reference "
        f"rule, and the system message repeats the headline beside it: {result.reason}"
    )


def test_reads_notebook_path_for_notebook_edit(tmp_path):
    file_path = write_python_file_with_line_count(tmp_path, "notebook.py", 250)
    result = line_count_limit_guard_handler.handle(
        {"tool_name": "NotebookEdit", "tool_input": {"notebook_path": str(file_path)}}
    )
    assert result is not None
    assert result.decision == "block"


def test_silent_under_threshold(tmp_path):
    file_path = write_python_file_with_line_count(tmp_path, "small.py", 50)
    result = line_count_limit_guard_handler.handle(
        {"tool_name": "Write", "tool_input": {"file_path": str(file_path)}}
    )
    assert result is None


def test_ignores_non_applicable_tool(tmp_path):
    file_path = write_python_file_with_line_count(tmp_path, "over.py", 250)
    result = line_count_limit_guard_handler.handle(
        {"tool_name": "Bash", "tool_input": {"file_path": str(file_path)}}
    )
    assert result is None


def test_ignores_non_code_extension(tmp_path):
    file_path = write_python_file_with_line_count(tmp_path, "notes.txt", 500)
    result = line_count_limit_guard_handler.handle(
        {"tool_name": "Write", "tool_input": {"file_path": str(file_path)}}
    )
    assert result is None


def test_blocks_a_fresh_over_limit_file_in_a_grandfathering_repository(tmp_path):
    record_line_counts(tmp_path, json.dumps({"legacy.py": 400}))
    file_path = write_python_file_with_line_count(tmp_path, "fresh.py", 201)
    result = handle_edit_of(file_path)
    assert result is not None
    assert result.decision == "block"
    assert "201" in result.reason


def test_passes_a_grandfathered_file_still_at_its_recorded_count(tmp_path):
    record_line_counts(tmp_path, json.dumps({"legacy.py": 400}))
    file_path = write_python_file_with_line_count(tmp_path, "legacy.py", 400)
    assert handle_edit_of(file_path) is None


def test_passes_a_grandfathered_file_that_shrank_toward_the_limit(tmp_path):
    record_line_counts(tmp_path, json.dumps({"legacy.py": 400}))
    file_path = write_python_file_with_line_count(tmp_path, "legacy.py", 250)
    assert handle_edit_of(file_path) is None


def test_blocks_one_line_of_growth_past_the_grandfathered_ceiling(tmp_path):
    record_line_counts(tmp_path, json.dumps({"legacy.py": 400}))
    file_path = write_python_file_with_line_count(tmp_path, "legacy.py", 401)
    result = handle_edit_of(file_path)
    assert result is not None
    assert result.decision == "block"
    assert "401" in result.reason
    assert "400" in result.reason


def test_the_worktree_baseline_grants_what_its_parent_checkout_withholds(tmp_path):
    record_line_counts(tmp_path, json.dumps({}))
    worktree_root = record_line_counts(
        tmp_path / ".worktrees" / "branch", json.dumps({"legacy.py": 400})
    )
    file_path = write_python_file_with_line_count(worktree_root, "legacy.py", 250)
    assert handle_edit_of(file_path) is None, (
        "the hook must read the baseline of the checkout the file lives in; "
        "reading the parent checkout's baseline blocks every grandfathered file "
        "edited inside a worktree"
    )


def test_a_parent_checkout_baseline_cannot_grant_a_worktree_file_its_ceiling(tmp_path):
    record_line_counts(
        tmp_path, json.dumps({".worktrees/branch/legacy.py": 400, "legacy.py": 400})
    )
    worktree_root = record_line_counts(
        tmp_path / ".worktrees" / "branch", json.dumps({})
    )
    file_path = write_python_file_with_line_count(worktree_root, "legacy.py", 250)
    result = handle_edit_of(file_path)
    assert result is not None
    assert result.decision == "block"


@pytest.mark.parametrize(
    "baseline_text",
    [
        '{"legacy.py": 400',
        '["legacy.py"]',
        '{"legacy.py": "400"}',
        '{"legacy.py": 400.5}',
        '{"legacy.py": true}',
    ],
)
def test_unusable_baseline_data_grants_no_ceiling(tmp_path, baseline_text):
    record_line_counts(tmp_path, baseline_text)
    file_path = write_python_file_with_line_count(tmp_path, "legacy.py", 250)
    result = handle_edit_of(file_path)
    assert result is not None
    assert result.decision == "block"
