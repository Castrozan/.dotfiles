import pytest
from workspace_checks.comments import (
    check_workspace_file_no_comments_assertion,
)


def write_and_check(tmp_path, file_name, source):
    (tmp_path / file_name).write_text(source)
    return check_workspace_file_no_comments_assertion(tmp_path, file_name)


def test_a_trailing_noqa_directive_passes(tmp_path):
    result = write_and_check(
        tmp_path,
        "suppressed_import.py",
        "import sys\n\nfrom late_module import helper  # noqa: E402\n\n\n"
        "def resolve_helper():\n    return helper(sys.argv)\n",
    )
    assert result.passed
    assert result.detail == "no comments found"


@pytest.mark.parametrize(
    ("file_name", "source"),
    [
        pytest.param(
            "bare_noqa.py",
            "def build_account_label(account):  # noqa\n    return account.label\n",
            id="a_bare_noqa_directive_passes",
        ),
        pytest.param(
            "typed.py",
            "def read_account_total(source):\n    return source.total  # type: ignore[attr-defined]\n",
            id="a_type_ignore_directive_passes",
        ),
        pytest.param(
            "covered.py",
            "def unreachable_account_branch():  # pragma: no cover\n    return None\n",
            id="a_coverage_pragma_passes",
        ),
        pytest.param(
            "formatted.py",
            "# fmt: off\nACCOUNT_COLUMNS = [1, 2, 3]\n# fmt: on\n",
            id="a_formatter_directive_passes",
        ),
        pytest.param(
            "encoded.py",
            "# -*- coding: utf-8 -*-\nACCOUNT_LABEL = 'conta'\n",
            id="an_encoding_declaration_passes",
        ),
    ],
)
def test_each_required_tooling_directive_passes(tmp_path, file_name, source):
    result = write_and_check(tmp_path, file_name, source)
    assert result.passed


def test_an_explanatory_comment_beside_a_directive_still_fails(tmp_path):
    result = write_and_check(
        tmp_path,
        "mixed.py",
        "import sys  # noqa: F401\n\n\n"
        "def resolve_account_label(account):\n"
        "    # strip the trailing separator first\n"
        "    return account.label.rstrip('/')\n",
    )
    assert not result.passed
    assert result.detail == "found: ['comment on line 5']"


def test_a_comment_that_merely_mentions_a_directive_word_still_fails(tmp_path):
    result = write_and_check(
        tmp_path,
        "mentions.py",
        "def resolve_account_label(account):\n"
        "    # noqa would silence this, but the rule is real\n"
        "    return account.label\n",
    )
    assert not result.passed
