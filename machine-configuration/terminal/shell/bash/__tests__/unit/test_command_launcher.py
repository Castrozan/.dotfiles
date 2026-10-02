import json
import shlex
from pathlib import Path

import pytest

from command_launcher_support import run_launcher


def test_multiword_query_executes_highest_ranked_alias(launcher_environment):
    launcher_environment["HSTR_RESULTS"] = json.dumps(["vt_test", "vt_prod"])
    result = run_launcher(
        launcher_environment,
        "alias vt_test='printf test'\nalias vt_prod='printf production'\ncx vt test",
    )
    assert result.returncode == 0
    assert result.stdout == "test"
    assert result.stderr == "vt_test\n"
    assert Path(
        launcher_environment["HSTR_ARGUMENT_FILE"]
    ).read_text().splitlines() == [
        "--non-interactive",
        "vt",
        "test",
    ]
    assert (
        Path(launcher_environment["HSTR_CONFIGURATION_FILE"]).read_text()
        == "keywords-matching"
    )


def test_recalled_function_changes_the_caller_directory(launcher_environment, tmp_path):
    destination = tmp_path / "destination with spaces"
    destination.mkdir()
    launcher_environment["HSTR_RESULTS"] = json.dumps(["enter_project"])
    result = run_launcher(
        launcher_environment,
        f"enter_project() {{ cd {shlex.quote(str(destination))}; }}\n"
        "cx project\nprintf '%s' \"$PWD\"",
    )
    assert result.returncode == 0
    assert result.stdout == str(destination)


def test_recalled_command_preserves_quoting_and_exit_status(launcher_environment):
    launcher_environment["HSTR_RESULTS"] = json.dumps(
        ["printf '%s' 'two  spaces'; exit 7"]
    )
    result = run_launcher(launcher_environment, "cx spaces")
    assert result.returncode == 7
    assert result.stdout == "two  spaces"


def test_multiline_command_is_executed_as_one_record(launcher_environment):
    launcher_environment["HSTR_RESULTS"] = json.dumps(["printf '%s' 'first\nsecond'"])
    result = run_launcher(launcher_environment, "cx second")
    assert result.returncode == 0
    assert result.stdout == "first\nsecond"


@pytest.mark.parametrize("results", [[], ["cx vt test", "cx", "z vt test", "z"]])
def test_empty_or_launcher_only_results_do_not_execute(launcher_environment, results):
    launcher_environment["HSTR_RESULTS"] = json.dumps(results)
    result = run_launcher(launcher_environment, "cx vt test")
    assert result.returncode == 1
    assert result.stdout == ""
    assert "no matching command" in result.stderr


def test_driver_failure_never_executes_partial_output(launcher_environment):
    launcher_environment.update(
        HSTR_RESULTS=json.dumps(["printf wrong"]), HSTR_EXIT_STATUS="6"
    )
    result = run_launcher(launcher_environment, "cx wrong")
    assert result.returncode == 6
    assert result.stdout == ""


def test_launcher_entries_are_skipped_before_executing(launcher_environment):
    launcher_environment["HSTR_RESULTS"] = json.dumps(
        ["cx vt test", "z vt test", "", "vt_test"]
    )
    result = run_launcher(
        launcher_environment, "alias vt_test='printf test'\ncx vt test"
    )
    assert result.returncode == 0
    assert result.stdout == "test"


def test_indirect_recursion_is_refused(launcher_environment):
    launcher_environment["HSTR_RESULTS"] = json.dumps(["recall_again"])
    result = run_launcher(
        launcher_environment, "recall_again() { cx recursive; }\ncx recursive"
    )
    assert result.returncode == 2
    assert "recursive command recall refused" in result.stderr


@pytest.mark.parametrize(
    ("commands", "expected_status", "expected_message"),
    [
        ("cx", 2, "Usage: cx"),
        ("unset HISTFILE\ncx test", 1, "command history is disabled"),
        ("PATH=/missing\ncx test", 1, "command history ranker is unavailable"),
    ],
)
def test_invalid_invocations_fail_explicitly(
    launcher_environment, commands, expected_status, expected_message
):
    result = run_launcher(launcher_environment, commands)
    assert result.returncode == expected_status
    assert expected_message in result.stderr
