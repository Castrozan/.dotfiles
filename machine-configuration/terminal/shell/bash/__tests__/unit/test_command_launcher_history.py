import json
import shlex
from pathlib import Path

from command_launcher_support import run_launcher


def test_history_preserves_repeat_executions_with_timestamps(launcher_environment):
    result = run_launcher(
        launcher_environment,
        "set -o history\nhistory -c\n"
        "history -s vt_test\n_history_prompt_command\n"
        "history -s vt_test\n_history_prompt_command\n"
        "_history_prompt_command\n",
    )
    assert result.returncode == 0
    saved_history = Path(launcher_environment["HISTFILE"]).read_text().splitlines()
    assert saved_history.count("vt_test") == 2
    assert sum(line.startswith("#") for line in saved_history) == 2
    assert not any("%F" in line for line in saved_history)


def test_saved_history_preserves_quoted_whitespace(launcher_environment):
    recalled_command = "printf '%s' 'two  spaces'"
    result = run_launcher(
        launcher_environment,
        "set -o history\nhistory -c\n"
        f"history -s {shlex.quote(recalled_command + '   ')}\n"
        "_history_prompt_command\n",
    )
    assert result.returncode == 0
    assert recalled_command in Path(launcher_environment["HISTFILE"]).read_text()


def test_recalled_command_is_recorded_under_its_original_name(launcher_environment):
    launcher_environment["HSTR_RESULTS"] = json.dumps(["vt_test"])
    result = run_launcher(
        launcher_environment,
        "alias vt_test='true'\nset -o history\nhistory -c\n"
        "history -s 'cx vt test'\ncx vt test\n_history_prompt_command\n",
    )
    assert result.returncode == 0
    saved_history = Path(launcher_environment["HISTFILE"]).read_text().splitlines()
    assert saved_history.count("vt_test") == 1


def test_unrecorded_invocation_does_not_add_the_recalled_command(launcher_environment):
    launcher_environment["HSTR_RESULTS"] = json.dumps(["vt_test"])
    result = run_launcher(
        launcher_environment,
        "alias vt_test='true'\nset -o history\nhistory -c\n"
        "history -s earlier\n_history_prompt_command\n"
        "cx vt test\n_history_prompt_command\n",
    )
    assert result.returncode == 0
    saved_history = Path(launcher_environment["HISTFILE"]).read_text().splitlines()
    assert "vt_test" not in saved_history
