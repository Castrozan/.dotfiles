from workspace_checks.comments import (
    check_workspace_file_no_comments_assertion,
)


def test_a_hash_inside_a_string_literal_is_not_a_comment(tmp_path):
    (tmp_path / "title_heading.py").write_text(
        'def title_heading():\n    return "# Title"\n'
    )
    result = check_workspace_file_no_comments_assertion(tmp_path, "title_heading.py")
    assert result.passed
    assert result.detail == "no comments found"


def test_a_shebang_on_line_one_alone_passes(tmp_path):
    (tmp_path / "shebang_only.py").write_text(
        "#!/usr/bin/env python3\n"
        "def normalize_account_name(raw_name):\n"
        "    return raw_name.strip()\n"
    )
    result = check_workspace_file_no_comments_assertion(tmp_path, "shebang_only.py")
    assert result.passed
    assert result.detail == "no comments found"


def test_a_shebang_plus_a_later_comment_fails_naming_only_the_later_line(tmp_path):
    (tmp_path / "shebang_and_comment.py").write_text(
        "#!/usr/bin/env python3\n"
        "def normalize_account_name(raw_name):\n"
        "    # explain\n"
        "    return raw_name.strip()\n"
    )
    result = check_workspace_file_no_comments_assertion(
        tmp_path, "shebang_and_comment.py"
    )
    assert not result.passed
    assert result.detail == "found: ['comment on line 3']"


def test_more_than_one_violation_is_reported_in_line_order(tmp_path):
    (tmp_path / "multiple_violations.py").write_text(
        "def normalize_account_name(raw_name):\n"
        '    """Return the normalized name."""\n'
        "    # explain\n"
        "    return raw_name.strip()  # trim\n"
    )
    result = check_workspace_file_no_comments_assertion(
        tmp_path, "multiple_violations.py"
    )
    assert not result.passed
    assert result.detail == (
        "found: ['docstring on line 2', 'comment on line 3', 'comment on line 4']"
    )


def test_a_missing_path_fails_with_file_does_not_exist(tmp_path):
    result = check_workspace_file_no_comments_assertion(tmp_path, "absent.py")
    assert not result.passed
    assert result.detail == "file does not exist"


def test_unparseable_python_fails_with_file_could_not_be_parsed(tmp_path):
    (tmp_path / "broken.py").write_text("def broken(\n    pass\n")
    result = check_workspace_file_no_comments_assertion(tmp_path, "broken.py")
    assert not result.passed
    assert result.detail == "file could not be parsed"


def test_a_non_python_file_still_uses_the_substring_path(tmp_path):
    (tmp_path / "notes.js").write_text("// note\n")
    result = check_workspace_file_no_comments_assertion(tmp_path, "notes.js")
    assert not result.passed
    assert result.detail == "found: ['// ']"
