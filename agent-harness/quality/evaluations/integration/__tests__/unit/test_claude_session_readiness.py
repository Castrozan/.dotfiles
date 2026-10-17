import subprocess

import pytest

from runner.execution import claude_session_readiness


@pytest.mark.parametrize(
    ("output", "returncode", "failure"),
    [
        ('{"loggedIn":true}', 0, None),
        ('{"loggedIn":false}', 1, "not authenticated"),
        ('{"loggedIn":true}', 1, "did not confirm access"),
        ("{}", 0, "did not confirm access"),
        ('{"loggedIn":"true"}', 0, "did not confirm access"),
        ("not json", 1, "valid JSON"),
        ("[]", 0, "not return an object"),
    ],
)
def test_authentication_requires_a_successful_affirmative_status(
    monkeypatch, tmp_path, output, returncode, failure
):
    monkeypatch.setattr(
        claude_session_readiness.subprocess,
        "run",
        lambda *arguments, **options: subprocess.CompletedProcess(
            arguments, returncode, output, "sensitive diagnostic"
        ),
    )

    result = claude_session_readiness.claude_authentication_failure(tmp_path)

    if failure is None:
        assert result is None
    else:
        assert failure in result
        assert "sensitive diagnostic" not in result


@pytest.mark.parametrize(
    "failure",
    [FileNotFoundError("missing"), subprocess.TimeoutExpired("claude", 15)],
)
def test_authentication_probe_failure_is_reported_without_details(
    monkeypatch, tmp_path, failure
):
    def run_command(*arguments, **options):
        raise failure

    monkeypatch.setattr(claude_session_readiness.subprocess, "run", run_command)

    assert claude_session_readiness.claude_authentication_failure(tmp_path) == (
        "Claude authentication status could not be checked"
    )


def test_authentication_probe_runs_in_the_disposable_scenario_workspace(
    monkeypatch, tmp_path
):
    def run_command(arguments, **options):
        assert options["cwd"] == tmp_path
        return subprocess.CompletedProcess(arguments, 0, '{"loggedIn":true}', "")

    monkeypatch.setattr(claude_session_readiness.subprocess, "run", run_command)

    assert claude_session_readiness.claude_authentication_failure(tmp_path) is None
