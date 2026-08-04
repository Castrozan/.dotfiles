import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hook_module_loader import import_hyphenated_hook_module

line_count_limit_guard_handler = import_hyphenated_hook_module(
    "line_count_limit_guard_handler"
)


def write_python_file_with_line_count(
    parent_directory: Path, file_basename: str, line_count: int
) -> Path:
    file_path = parent_directory / file_basename
    file_path.write_text("\n".join(f"line_{n}" for n in range(line_count)) + "\n")
    return file_path


def test_blocks_edit_of_code_file_over_threshold(tmp_path):
    file_path = write_python_file_with_line_count(tmp_path, "over.py", 250)
    result = line_count_limit_guard_handler.handle(
        {"tool_name": "Edit", "tool_input": {"file_path": str(file_path)}}
    )
    assert result is not None
    assert result.decision == "block"
    assert "250" in result.reason
    assert "BLOCKED" in result.system_message


def test_the_block_states_what_is_blocked_and_points_at_the_detail(tmp_path):
    file_path = write_python_file_with_line_count(tmp_path, "over.py", 250)
    result = line_count_limit_guard_handler.handle(
        {"tool_name": "Edit", "tool_input": {"file_path": str(file_path)}}
    )
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
