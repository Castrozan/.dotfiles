import json
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from command_launcher_support import (
    BASH,
    BASH_DIRECTORY,
    HISTORY,
    LAUNCHER,
    run_launcher,
)

Z_LAUNCHER = BASH_DIRECTORY / "scripts/command-launcher/z-command-launcher.sh"
ZOXIDE_HELPERS = (
    "__zoxide_z_prefix='z#'\n"
    "__zoxide_doctor() { :; }\n"
    "__zoxide_pwd() { builtin pwd -L; }\n"
    '__zoxide_cd() { builtin cd -- "$@"; }\n'
    "__zoxide_z() { printf 'native:%s' \"$*\"; return 9; }\n"
    f". {shlex.quote(str(Z_LAUNCHER))}\n"
)


@pytest.fixture
def z_launcher_environment(launcher_environment, tmp_path):
    driver = tmp_path / "bin/zoxide"
    driver.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "Path(os.environ['ZOXIDE_ARGUMENT_FILE']).write_text(json.dumps(sys.argv[1:]))\n"
        "status = int(os.environ['ZOXIDE_QUERY_STATUS'])\n"
        "print(os.environ['ZOXIDE_QUERY_OUTPUT'], file=sys.stderr if status else sys.stdout)\n"
        "sys.exit(status)\n"
    )
    driver.chmod(0o755)
    launcher_environment.update(
        ZOXIDE_ARGUMENT_FILE=str(tmp_path / "zoxide-arguments"),
        ZOXIDE_QUERY_STATUS="1",
        ZOXIDE_QUERY_OUTPUT="zoxide: no match found",
        HSTR_RESULTS=json.dumps(["vt_test"]),
    )
    return launcher_environment


@pytest.mark.parametrize("command_status", [0, 7])
def test_no_directory_match_recalls_an_alias(z_launcher_environment, command_status):
    result = run_launcher(
        z_launcher_environment,
        ZOXIDE_HELPERS
        + f"alias vt_test='printf test; return {command_status}'\nz vt test",
    )
    assert result.returncode == command_status
    assert result.stdout == "test"
    assert result.stderr == "vt_test\n"
    arguments = json.loads(
        Path(z_launcher_environment["ZOXIDE_ARGUMENT_FILE"]).read_text()
    )
    assert arguments[:2] == ["query", "--exclude"]
    assert arguments[3:] == ["--", "vt", "test"]


def test_directory_match_wins_and_changes_the_caller_directory(
    z_launcher_environment, tmp_path
):
    destination = tmp_path / "vt test"
    destination.mkdir()
    z_launcher_environment.update(
        ZOXIDE_QUERY_STATUS="0", ZOXIDE_QUERY_OUTPUT=str(destination)
    )
    result = run_launcher(
        z_launcher_environment, ZOXIDE_HELPERS + "z vt test\nprintf '%s' \"$PWD\""
    )
    assert result.returncode == 0
    assert result.stdout == str(destination)
    assert result.stderr == ""
    assert not Path(z_launcher_environment["HSTR_ARGUMENT_FILE"]).exists()


@pytest.mark.parametrize(
    "arguments", ["", "-", "-- absent", "absent/path", "z#absent/"]
)
def test_directory_syntax_keeps_native_behavior(z_launcher_environment, arguments):
    result = run_launcher(z_launcher_environment, ZOXIDE_HELPERS + f"z {arguments}")
    assert result.returncode == 9
    assert result.stdout == f"native:{arguments}"
    assert not Path(z_launcher_environment["ZOXIDE_ARGUMENT_FILE"]).exists()
    assert not Path(z_launcher_environment["HSTR_ARGUMENT_FILE"]).exists()


def test_existing_relative_directory_keeps_native_behavior(
    z_launcher_environment, tmp_path
):
    (tmp_path / "destination").mkdir()
    result = run_launcher(
        z_launcher_environment,
        ZOXIDE_HELPERS + f"cd {shlex.quote(str(tmp_path))}\nz destination",
    )
    assert result.returncode == 9
    assert result.stdout == "native:destination"
    assert not Path(z_launcher_environment["ZOXIDE_ARGUMENT_FILE"]).exists()


def test_directory_backend_error_never_recalls_a_command(z_launcher_environment):
    z_launcher_environment.update(
        ZOXIDE_QUERY_STATUS="7", ZOXIDE_QUERY_OUTPUT="zoxide: database error"
    )
    result = run_launcher(z_launcher_environment, ZOXIDE_HELPERS + "z vt test")
    assert result.returncode == 7
    assert result.stdout == ""
    assert result.stderr == "zoxide: database error\n"
    assert not Path(z_launcher_environment["HSTR_ARGUMENT_FILE"]).exists()


def test_failed_directory_change_never_recalls_a_command(
    z_launcher_environment, tmp_path
):
    z_launcher_environment.update(
        ZOXIDE_QUERY_STATUS="0", ZOXIDE_QUERY_OUTPUT=str(tmp_path / "absent")
    )
    result = run_launcher(z_launcher_environment, ZOXIDE_HELPERS + "z vt test")
    assert result.returncode == 1
    assert result.stdout == ""
    assert not Path(z_launcher_environment["HSTR_ARGUMENT_FILE"]).exists()


def test_recalled_function_changes_the_caller_directory(
    z_launcher_environment, tmp_path
):
    z_launcher_environment["HSTR_RESULTS"] = json.dumps(["enter_project"])
    result = run_launcher(
        z_launcher_environment,
        ZOXIDE_HELPERS + f"enter_project() {{ cd {shlex.quote(str(tmp_path))}; }}\n"
        "z enter project\nprintf '%s' \"$PWD\"",
    )
    assert result.returncode == 0
    assert result.stdout == str(tmp_path)


def test_indirect_z_recursion_is_refused(z_launcher_environment):
    z_launcher_environment["HSTR_RESULTS"] = json.dumps(["recall_again"])
    result = run_launcher(
        z_launcher_environment,
        ZOXIDE_HELPERS + "recall_again() { z recursive; }\nz recursive",
    )
    assert result.returncode == 2
    assert "recursive command recall refused" in result.stderr


def test_z_recall_learns_the_underlying_command(z_launcher_environment):
    result = subprocess.run(
        [BASH, "--noprofile", "--norc", "-i"],
        input=(
            f". {shlex.quote(str(HISTORY))}\n"
            f". {shlex.quote(str(LAUNCHER))}\n"
            + ZOXIDE_HELPERS
            + "alias vt_test='true'\nhistory -c\nvt_test\nz vt test\n z vt test\nexit\n"
        ),
        env=z_launcher_environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    saved_history = Path(z_launcher_environment["HISTFILE"]).read_text().splitlines()
    assert saved_history.count("vt_test") == 2
    assert saved_history.count("z vt test") == 0


def test_no_match_falls_back_with_errexit_enabled(z_launcher_environment):
    result = run_launcher(
        z_launcher_environment,
        ZOXIDE_HELPERS + "alias vt_test='printf test'\nset -e\nz vt test",
    )
    assert result.returncode == 0
    assert result.stdout == "test"
