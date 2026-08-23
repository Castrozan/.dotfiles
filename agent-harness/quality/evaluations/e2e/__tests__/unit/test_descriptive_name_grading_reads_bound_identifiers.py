from e2e_assertions_naming import check_workspace_file_descriptive_names_assertion


def test_a_file_whose_bound_names_are_all_descriptive_passes(tmp_path):
    (tmp_path / "totals.py").write_text(
        "def calculate_total(prices):\n"
        "    running_total = 0\n"
        "    for price in prices:\n"
        "        running_total += price\n"
        "    return running_total\n"
    )
    result = check_workspace_file_descriptive_names_assertion(tmp_path, "totals.py")
    assert result.passed
    assert result.detail == "all bound names are descriptive"


def test_a_single_character_loop_target_fails_and_the_detail_names_it(tmp_path):
    (tmp_path / "ages.py").write_text(
        "def sum_ages(users):\n"
        "    total = 0\n"
        "    for u in users:\n"
        "        total += u.age\n"
        "    return total\n"
    )
    result = check_workspace_file_descriptive_names_assertion(tmp_path, "ages.py")
    assert not result.passed
    assert result.detail == "not descriptive: ['u']"


def test_an_underscore_discard_target_passes(tmp_path):
    (tmp_path / "unpacking.py").write_text(
        "def ignore_first_element(pairs):\n    _, second = pairs\n    return second\n"
    )
    result = check_workspace_file_descriptive_names_assertion(tmp_path, "unpacking.py")
    assert result.passed
    assert result.detail == "all bound names are descriptive"


def test_a_compound_name_with_an_embedded_abbreviation_fails_and_names_it(tmp_path):
    (tmp_path / "messages.py").write_text(
        "def extract_recent_messages(entries):\n"
        "    filtered_msg_list = []\n"
        "    for entry in entries:\n"
        "        filtered_msg_list.append(entry)\n"
        "    return filtered_msg_list\n"
    )
    result = check_workspace_file_descriptive_names_assertion(tmp_path, "messages.py")
    assert not result.passed
    assert result.detail == "not descriptive: ['filtered_msg_list']"


def test_a_plural_abbreviation_fails(tmp_path):
    (tmp_path / "notifications.py").write_text(
        "def collect_notifications(source):\n"
        "    msgs = []\n"
        "    for notification in source:\n"
        "        msgs.append(notification)\n"
        "    return msgs\n"
    )
    result = check_workspace_file_descriptive_names_assertion(
        tmp_path, "notifications.py"
    )
    assert not result.passed
    assert result.detail == "not descriptive: ['msgs']"


def test_reading_a_short_builtin_does_not_fail(tmp_path):
    (tmp_path / "summary.py").write_text(
        "def summarize(items, record):\n    return len(items), id(record)\n"
    )
    result = check_workspace_file_descriptive_names_assertion(tmp_path, "summary.py")
    assert result.passed
    assert result.detail == "all bound names are descriptive"


def test_a_missing_path_fails_with_file_does_not_exist(tmp_path):
    result = check_workspace_file_descriptive_names_assertion(tmp_path, "absent.py")
    assert not result.passed
    assert result.detail == "file does not exist"


def test_a_non_python_file_passes(tmp_path):
    (tmp_path / "notes.txt").write_text("u = 1\n")
    result = check_workspace_file_descriptive_names_assertion(tmp_path, "notes.txt")
    assert result.passed
    assert result.detail == "no name analysis available"


def test_dunder_init_and_self_are_not_flagged(tmp_path):
    (tmp_path / "widget.py").write_text(
        "class Widget:\n"
        "    def __init__(self, capacity):\n"
        "        self.capacity = capacity\n"
    )
    result = check_workspace_file_descriptive_names_assertion(tmp_path, "widget.py")
    assert result.passed
    assert result.detail == "all bound names are descriptive"


def test_a_self_attribute_assignment_fails_on_a_single_character_name(tmp_path):
    (tmp_path / "counter.py").write_text(
        "class Counter:\n    def __init__(self):\n        self.n = 1\n"
    )
    result = check_workspace_file_descriptive_names_assertion(tmp_path, "counter.py")
    assert not result.passed
    assert result.detail == "not descriptive: ['n']"


def test_unparseable_python_fails_with_file_could_not_be_parsed(tmp_path):
    (tmp_path / "broken.py").write_text("def broken(:\n    pass\n")
    result = check_workspace_file_descriptive_names_assertion(tmp_path, "broken.py")
    assert not result.passed
    assert result.detail == "file could not be parsed"


def test_a_word_that_legitimately_ends_in_s_is_not_a_false_positive(tmp_path):
    (tmp_path / "registry.py").write_text("addresses = []\nclasses = []\n")
    result = check_workspace_file_descriptive_names_assertion(tmp_path, "registry.py")
    assert result.passed
    assert result.detail == "all bound names are descriptive"


def test_a_single_character_padded_with_underscores_is_not_exempt_as_a_dunder(tmp_path):
    source_path = tmp_path / "padded.py"
    source_path.write_text("__n__ = 1\n")
    outcome = check_workspace_file_descriptive_names_assertion(tmp_path, "padded.py")
    assert outcome.passed is False
    assert "__n__" in outcome.detail


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


def test_a_single_character_import_alias_is_judged(tmp_path):
    source_path = tmp_path / "aliased.py"
    source_path.write_text("import statistics as s\n\n\ntotal = s\n")
    outcome = check_workspace_file_descriptive_names_assertion(tmp_path, "aliased.py")
    assert outcome.passed is False
    assert "'s'" in outcome.detail


def test_an_abbreviated_import_alias_is_judged(tmp_path):
    source_path = tmp_path / "abbreviated.py"
    source_path.write_text("import configuration as cfg\n\n\nloaded = cfg\n")
    outcome = check_workspace_file_descriptive_names_assertion(
        tmp_path, "abbreviated.py"
    )
    assert outcome.passed is False
    assert "cfg" in outcome.detail


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
