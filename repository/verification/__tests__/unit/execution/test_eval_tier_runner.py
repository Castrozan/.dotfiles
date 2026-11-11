import os
import pathlib
import shutil
import subprocess

import pytest

HARNESS_TESTS_ROOT = pathlib.Path(__file__).resolve().parents[3]
EVALS_TIER_LIBRARY = HARNESS_TESTS_ROOT / "runner" / "evals.sh"

MODERN_BASH_CANDIDATE_PATHS = (
    "/run/current-system/sw/bin/bash",
    f"/etc/profiles/per-user/{os.environ.get('USER', '')}/bin/bash",
    "/opt/homebrew/bin/bash",
)

SKIPPED_STATUS = 77
SUBPROCESS_TIMEOUT_SECONDS = 30

TIER_FUNCTIONS = ("_run_evals_tier", "_run_integration_tier", "_run_e2e_tier")
SESSION_SANDBOX_TIER_FUNCTIONS = ("_run_integration_tier", "_run_e2e_tier")


def _resolve_modern_bash_absolute_path() -> str:
    for candidate in [shutil.which("bash"), *MODERN_BASH_CANDIDATE_PATHS]:
        if not candidate or not os.path.exists(candidate):
            continue
        probe = subprocess.run(
            [candidate, "-c", "echo ${BASH_VERSINFO[0]}"],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
        )
        if probe.stdout.strip().isdigit() and int(probe.stdout.strip()) >= 4:
            return candidate
    pytest.skip("no bash >= 4 available to exercise the evals tier library")


def _run_tier_without_its_tools(tier_function: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            _resolve_modern_bash_absolute_path(),
            "-c",
            f'source "{EVALS_TIER_LIBRARY}"; {tier_function}',
        ],
        env={"PATH": "", "REPO_DIR": str(HARNESS_TESTS_ROOT.parents[1])},
        capture_output=True,
        text=True,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
    )


@pytest.mark.parametrize("tier_function", TIER_FUNCTIONS)
def test_a_missing_tool_reports_a_skip_instead_of_a_pass(tier_function):
    completed = _run_tier_without_its_tools(tier_function)

    assert completed.returncode == SKIPPED_STATUS
    assert completed.returncode != 0, (
        f"{tier_function} returned success on a machine that cannot run it"
    )


@pytest.mark.parametrize("tier_function", TIER_FUNCTIONS)
def test_a_skip_says_which_tool_is_missing(tier_function):
    completed = _run_tier_without_its_tools(tier_function)

    assert "SKIP:" in completed.stderr
    assert "not installed" in completed.stderr


def _install_recording_evaluation_command(
    tool_directory: pathlib.Path, exit_status: int
) -> pathlib.Path:
    recorded_arguments = tool_directory / "recorded-arguments"
    command = tool_directory / "dotfiles-evals"
    command.write_text(
        f'#!/bin/sh\nprintf "%s\\n" "$@" > "{recorded_arguments}"\nexit {exit_status}\n'
    )
    command.chmod(0o755)
    return recorded_arguments


def _install_session_sandbox_command(tool_directory: pathlib.Path) -> None:
    sandbox = tool_directory / "bwrap"
    sandbox.write_text("#!/bin/sh\nexit 0\n")
    sandbox.chmod(0o755)


def _run_tier_in_tool_directory(
    tier_function: str, tool_directory: pathlib.Path, search_path: str, state_home: str
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            _resolve_modern_bash_absolute_path(),
            "-c",
            f'source "{EVALS_TIER_LIBRARY}"; {tier_function}',
        ],
        env={
            "PATH": search_path,
            "REPO_DIR": str(HARNESS_TESTS_ROOT.parents[1]),
            "XDG_STATE_HOME": state_home,
        },
        capture_output=True,
        text=True,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
    )


def _run_tier_with_recording_command(
    tier_function: str, tmp_path: pathlib.Path, exit_status: int
) -> tuple[subprocess.CompletedProcess, list[str]]:
    tool_directory = tmp_path / "bin"
    tool_directory.mkdir()
    recorded_arguments = _install_recording_evaluation_command(
        tool_directory, exit_status
    )
    _install_session_sandbox_command(tool_directory)
    completed = _run_tier_in_tool_directory(
        tier_function,
        tool_directory,
        f"{tool_directory}:{os.environ['PATH']}",
        str(tmp_path / "state"),
    )
    return completed, recorded_arguments.read_text().splitlines()


def _run_tier_without_session_sandbox(
    tier_function: str, tmp_path: pathlib.Path
) -> tuple[subprocess.CompletedProcess, pathlib.Path]:
    tool_directory = tmp_path / "bin"
    tool_directory.mkdir()
    recorded_arguments = _install_recording_evaluation_command(tool_directory, 0)
    completed = _run_tier_in_tool_directory(
        tier_function, tool_directory, str(tool_directory), str(tmp_path / "state")
    )
    return completed, recorded_arguments


@pytest.mark.parametrize("tier_function", SESSION_SANDBOX_TIER_FUNCTIONS)
def test_a_tier_of_real_agent_sessions_skips_where_the_session_sandbox_is_absent(
    tier_function, tmp_path
):
    completed, recorded_arguments = _run_tier_without_session_sandbox(
        tier_function, tmp_path
    )

    assert completed.returncode == SKIPPED_STATUS
    assert "SKIP:" in completed.stderr
    assert "bwrap" in completed.stderr
    assert not recorded_arguments.exists()


def test_the_evals_tier_does_not_need_the_session_sandbox(tmp_path):
    completed, recorded_arguments = _run_tier_without_session_sandbox(
        "_run_evals_tier", tmp_path
    )

    assert completed.returncode == 0, completed.stderr
    assert recorded_arguments.exists()


@pytest.mark.parametrize("tier_function", TIER_FUNCTIONS)
def test_a_tier_writes_its_report_to_state_and_never_to_the_committed_results(
    tier_function, tmp_path
):
    _, arguments = _run_tier_with_recording_command(tier_function, tmp_path, 0)

    report_path = pathlib.Path(arguments[arguments.index("--relatorio") + 1])
    assert report_path.is_relative_to(tmp_path / "state")
    assert not report_path.is_relative_to(HARNESS_TESTS_ROOT.parents[1])


def test_each_tier_keeps_its_own_report(tmp_path):
    report_paths = set()
    for tier_function in TIER_FUNCTIONS:
        tier_directory = tmp_path / tier_function
        tier_directory.mkdir()
        _, arguments = _run_tier_with_recording_command(
            tier_function, tier_directory, 0
        )
        report_path = pathlib.Path(arguments[arguments.index("--relatorio") + 1])
        report_paths.add(report_path.relative_to(tier_directory / "state"))

    assert len(report_paths) == len(TIER_FUNCTIONS)


@pytest.mark.parametrize("tier_function", TIER_FUNCTIONS)
def test_an_invalid_measurement_fails_the_tier_without_relying_on_errexit(
    tier_function, tmp_path
):
    completed, _ = _run_tier_with_recording_command(tier_function, tmp_path, 1)

    assert completed.returncode == 1, (
        f"stdout: {completed.stdout}\nstderr: {completed.stderr}"
    )
