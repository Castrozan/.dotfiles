from e2e_assertions_naming import check_workspace_file_descriptive_names_assertion


def test_an_underscore_discard_target_passes(tmp_path):
    (tmp_path / "unpacking.py").write_text(
        "def ignore_first_element(pairs):\n    _, second = pairs\n    return second\n"
    )
    result = check_workspace_file_descriptive_names_assertion(tmp_path, "unpacking.py")
    assert result.passed
    assert result.detail == "all bound names are descriptive"


def test_a_second_discard_written_only_in_underscores_passes(tmp_path):
    source_path = tmp_path / "discards.py"
    source_path.write_text(
        "def count_pairs(pairs):\n"
        "    total = 0\n"
        "    for _, __ in pairs:\n"
        "        total += 1\n"
        "    return total\n"
    )
    outcome = check_workspace_file_descriptive_names_assertion(tmp_path, "discards.py")
    assert outcome.passed is True


def test_dunder_init_and_self_are_not_flagged(tmp_path):
    (tmp_path / "widget.py").write_text(
        "class Widget:\n"
        "    def __init__(self, capacity):\n"
        "        self.capacity = capacity\n"
    )
    result = check_workspace_file_descriptive_names_assertion(tmp_path, "widget.py")
    assert result.passed
    assert result.detail == "all bound names are descriptive"


def test_the_shortest_real_dunder_names_stay_exempt(tmp_path):
    source_path = tmp_path / "operators.py"
    source_path.write_text(
        "class Money:\n"
        "    def __eq__(self, other):\n"
        "        return True\n\n"
        "    def __or__(self, other):\n"
        "        return self\n"
    )
    outcome = check_workspace_file_descriptive_names_assertion(tmp_path, "operators.py")
    assert outcome.passed is True


def test_a_single_character_padded_with_underscores_is_not_exempt_as_a_dunder(tmp_path):
    source_path = tmp_path / "padded.py"
    source_path.write_text("__n__ = 1\n")
    outcome = check_workspace_file_descriptive_names_assertion(tmp_path, "padded.py")
    assert outcome.passed is False
    assert "__n__" in outcome.detail


def test_a_name_the_imported_module_chose_is_not_judged(tmp_path):
    source_path = tmp_path / "imported.py"
    source_path.write_text("from statistics import mean as arithmetic_mean\n")
    outcome = check_workspace_file_descriptive_names_assertion(tmp_path, "imported.py")
    assert outcome.passed is True


def test_a_conventional_two_letter_alias_passes(tmp_path):
    source_path = tmp_path / "conventional.py"
    source_path.write_text("import datetime as dt\n\n\nstamp = dt\n")
    outcome = check_workspace_file_descriptive_names_assertion(
        tmp_path, "conventional.py"
    )
    assert outcome.passed is True


def test_a_fixture_name_the_test_runner_supplies_is_not_judged(tmp_path):
    source_path = tmp_path / "fixture_user.py"
    source_path.write_text(
        "def test_a_report_is_written(tmp_path):\n"
        "    written_report = tmp_path / 'report.txt'\n"
        "    written_report.write_text('done')\n"
        "    assert written_report.exists()\n"
    )
    outcome = check_workspace_file_descriptive_names_assertion(
        tmp_path, "fixture_user.py"
    )
    assert outcome.passed is True
