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
