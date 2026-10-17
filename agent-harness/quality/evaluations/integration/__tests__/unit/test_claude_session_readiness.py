import subprocess

import pytest

import claude_session_readiness


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
    monkeypatch, output, returncode, failure
):
    monkeypatch.setattr(
        claude_session_readiness.subprocess,
        "run",
        lambda *arguments, **options: subprocess.CompletedProcess(
            arguments, returncode, output, "sensitive diagnostic"
        ),
    )

    result = claude_session_readiness.claude_authentication_failure()

    if failure is None:
        assert result is None
    else:
        assert failure in result
        assert "sensitive diagnostic" not in result


@pytest.mark.parametrize(
    "failure",
    [FileNotFoundError("missing"), subprocess.TimeoutExpired("claude", 15)],
)
def test_authentication_probe_failure_is_reported_without_details(monkeypatch, failure):
    def run_command(*arguments, **options):
        raise failure

    monkeypatch.setattr(claude_session_readiness.subprocess, "run", run_command)

    assert claude_session_readiness.claude_authentication_failure() == (
        "Claude authentication status could not be checked"
    )
