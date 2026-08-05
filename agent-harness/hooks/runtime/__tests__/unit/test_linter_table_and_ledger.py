import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lint"))

from lint_ledger import (  # noqa: E402
    append_edited_source_file,
    ledger_file_path_for_session,
    read_and_clear_edited_source_files,
)
from linter_table_by_extension import parse_ruff_output  # noqa: E402
from repo_native_lint_command_detection import (  # noqa: E402
    detect_repository_native_lint_command,
)


def test_ruff_parser_filters_out_all_checks_passed_success_line():
    assert parse_ruff_output("All checks passed!\n") == []


def test_ruff_parser_filters_out_found_n_errors_summary_line():
    assert parse_ruff_output("Found 3 errors.\n") == []


def test_ruff_parser_keeps_real_issue_lines():
    ruff_issue_output = (
        "example.py:1:1: F401 [*] `os` imported but unused\n"
        "example.py:5:80: E501 Line too long (95 > 88)\n"
        "Found 2 errors.\n"
    )
    assert parse_ruff_output(ruff_issue_output) == [
        "example.py:1:1: F401 [*] `os` imported but unused",
        "example.py:5:80: E501 Line too long (95 > 88)",
    ]


def test_ledger_append_then_read_and_clear_roundtrip_dedupes():
    session_id = "pytest-ledger-roundtrip"
    try:
        os.remove(ledger_file_path_for_session(session_id))
    except OSError:
        pass
    append_edited_source_file(session_id, "/a.py")
    append_edited_source_file(session_id, "/b.py")
    append_edited_source_file(session_id, "/a.py")
    assert read_and_clear_edited_source_files(session_id) == ["/a.py", "/b.py"]
    assert read_and_clear_edited_source_files(session_id) == []


def test_ledger_read_missing_returns_empty():
    assert read_and_clear_edited_source_files("pytest-ledger-absent-xyz") == []


def test_detects_package_json_lint_script(tmp_path):
    (tmp_path / "package.json").write_text('{"scripts": {"lint": "eslint ."}}')
    assert detect_repository_native_lint_command(str(tmp_path)) == "npm run lint"


def test_detects_makefile_lint_target(tmp_path):
    (tmp_path / "Makefile").write_text("lint:\n\truff check .\n")
    assert detect_repository_native_lint_command(str(tmp_path)) == "make lint"


def test_precommit_takes_precedence(tmp_path):
    (tmp_path / ".pre-commit-config.yaml").write_text("repos: []\n")
    (tmp_path / "Makefile").write_text("lint:\n")
    assert (
        detect_repository_native_lint_command(str(tmp_path))
        == "pre-commit run --all-files"
    )


def test_returns_none_without_native_tooling(tmp_path):
    assert detect_repository_native_lint_command(str(tmp_path)) is None
