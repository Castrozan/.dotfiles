import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "post-tool-use"))

from lint_on_edit_linter_table import parse_ruff_output  # noqa: E402


def test_ruff_parser_filters_out_all_checks_passed_success_line():
    ruff_success_output = "All checks passed!\n"

    parsed_issues = parse_ruff_output(ruff_success_output)

    assert parsed_issues == [], (
        "ruff prints 'All checks passed!' on success; parser must treat it as "
        "no-issues so the hook stays silent instead of reporting a fake issue"
    )


def test_ruff_parser_filters_out_found_n_errors_summary_line():
    ruff_summary_output = "Found 3 errors.\n"

    parsed_issues = parse_ruff_output(ruff_summary_output)

    assert parsed_issues == []


def test_ruff_parser_keeps_real_issue_lines():
    ruff_issue_output = (
        "example.py:1:1: F401 [*] `os` imported but unused\n"
        "example.py:5:80: E501 Line too long (95 > 88)\n"
        "Found 2 errors.\n"
    )

    parsed_issues = parse_ruff_output(ruff_issue_output)

    assert parsed_issues == [
        "example.py:1:1: F401 [*] `os` imported but unused",
        "example.py:5:80: E501 Line too long (95 > 88)",
    ]
