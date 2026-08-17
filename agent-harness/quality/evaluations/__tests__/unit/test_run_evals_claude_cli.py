import run_evals_claude_cli
from run_evals_claude_cli import run_claude_cli


class _FakeCompletedProcess:
    def __init__(self):
        self.returncode = 0
        self.stdout = "READY"
        self.stderr = ""


def test_prompt_is_delivered_via_stdin_not_as_an_argv_positional(monkeypatch):
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["input"] = kwargs.get("input")
        return _FakeCompletedProcess()

    monkeypatch.setattr(run_evals_claude_cli.subprocess, "run", fake_run)

    output, invoked = run_claude_cli(
        "GRADE THIS RESPONSE", model="haiku", no_tools=True
    )

    assert invoked is True
    assert output == "READY"
    assert captured["input"] == "GRADE THIS RESPONSE"
    assert "GRADE THIS RESPONSE" not in captured["cmd"]
    assert "--tools" in captured["cmd"]
    assert "--safe-mode" in captured["cmd"]


class _ProcessWithStderrChrome:
    def __init__(self):
        self.returncode = 0
        self.stdout = "research"
        self.stderr = (
            "Managed settings contain invalid entries "
            "(remaining valid policies are still enforced):"
        )


def test_successful_grade_uses_stdout_and_excludes_stderr_chrome(monkeypatch):
    monkeypatch.setattr(
        run_evals_claude_cli.subprocess,
        "run",
        lambda *args, **kwargs: _ProcessWithStderrChrome(),
    )

    output, invoked = run_claude_cli("route this", model="haiku", no_tools=True)

    assert invoked is True
    assert output == "research"


class _ProcessThatCrashedWithoutStdout:
    def __init__(self):
        self.returncode = 1
        self.stdout = ""
        self.stderr = "fatal: the model backend refused the request"


def test_failure_surfaces_stderr_when_stdout_is_empty(monkeypatch):
    monkeypatch.setattr(
        run_evals_claude_cli.subprocess,
        "run",
        lambda *args, **kwargs: _ProcessThatCrashedWithoutStdout(),
    )
    monkeypatch.setattr(run_evals_claude_cli.time, "sleep", lambda *args: None)

    output, invoked = run_claude_cli("do a thing", model="haiku")

    assert invoked is False
    assert "the model backend refused the request" in output


def test_session_limit_failure_is_not_retried(monkeypatch):
    invocations = []

    class SessionLimitProcess:
        returncode = 1
        stdout = ""
        stderr = "You've hit your session limit"

    def fake_run(*args, **kwargs):
        invocations.append(True)
        return SessionLimitProcess()

    monkeypatch.setattr(run_evals_claude_cli.subprocess, "run", fake_run)

    output, invoked = run_claude_cli("do a thing", model="haiku")

    assert invoked is False
    assert "session limit" in output
    assert len(invocations) == 1
