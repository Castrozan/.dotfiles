from contextlib import nullcontext

import pytest

import run_evals_subject_port as subject_port
from run_evals_subject_port import (
    NODE_RUNTIME_BINARY,
    NODE_RUNTIME_OVERRIDE,
    invoke_subject,
    is_retryable_failure,
    resolve_node_runtime,
)


class _CompletedProcess:
    returncode = 0
    stdout = ""
    stderr = ""


def test_resolution_prefers_the_override_then_path(monkeypatch):
    monkeypatch.setenv(NODE_RUNTIME_OVERRIDE, "/custom/agent-eval-provider")
    assert resolve_node_runtime() == "/custom/agent-eval-provider"

    monkeypatch.delenv(NODE_RUNTIME_OVERRIDE, raising=False)
    monkeypatch.setattr(subject_port.shutil, "which", lambda name: f"/bin/{name}")
    assert resolve_node_runtime() == f"/bin/{NODE_RUNTIME_BINARY}"


def test_resolution_refuses_when_the_runtime_is_missing(monkeypatch):
    monkeypatch.delenv(NODE_RUNTIME_OVERRIDE, raising=False)
    monkeypatch.setattr(subject_port.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="provider runtime"):
        resolve_node_runtime()


def test_retryable_failure_excludes_the_non_retryable_markers():
    assert is_retryable_failure("backend hiccup")
    assert not is_retryable_failure("You've hit your session limit")
    assert not is_retryable_failure("usage limit reached")
    assert not is_retryable_failure("not logged in")
    assert not is_retryable_failure("cannot enforce no_tools")


def test_success_returns_the_output_string(monkeypatch):
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["input"] = kwargs.get("input")
        captured["cwd"] = kwargs.get("cwd")
        captured["env"] = kwargs.get("env")
        captured["timeout"] = kwargs.get("timeout")
        return _CompletedProcess()

    monkeypatch.setattr(subject_port.subprocess, "run", fake_run)
    monkeypatch.setattr(subject_port, "resolve_node_runtime", lambda: "/bin/runtime")
    monkeypatch.setattr(
        subject_port,
        "read_result_file",
        lambda path: {"output": "the answer", "error": None},
    )

    output, invoked = invoke_subject("claude", prompt="q", model="haiku")

    assert invoked is True
    assert output == "the answer"
    assert "claude" in captured["input"]
    assert subject_port.EVAL_WORKING_DIRECTORY == captured["cwd"]
    assert captured["timeout"] == 125


def test_provider_error_with_a_retryable_marker_is_retried(monkeypatch):
    attempts = []
    results = iter(
        ({"output": None, "error": "backend hiccup"}, {"output": "ok", "error": None})
    )
    monkeypatch.setattr(subject_port.subprocess, "run", lambda cmd, **kw: None)
    monkeypatch.setattr(subject_port, "resolve_node_runtime", lambda: "/bin/runtime")
    monkeypatch.setattr(
        subject_port.time, "sleep", lambda *args: attempts.append("backoff")
    )
    monkeypatch.setattr(
        subject_port,
        "read_result_file",
        lambda path: next(results),
    )

    output, invoked = invoke_subject("claude", prompt="q")

    assert invoked is True
    assert output == "ok"
    assert len(attempts) == 1


def test_provider_error_with_a_non_retryable_marker_is_not_retried(monkeypatch):
    invocations = []
    monkeypatch.setattr(
        subject_port.subprocess,
        "run",
        lambda cmd, **kw: invocations.append(True) or None,
    )
    monkeypatch.setattr(subject_port, "resolve_node_runtime", lambda: "/bin/runtime")
    monkeypatch.setattr(
        subject_port,
        "read_result_file",
        lambda path: {"output": None, "error": "usage limit reached"},
    )

    output, invoked = invoke_subject("claude", prompt="q")

    assert invoked is False
    assert "usage limit" in output
    assert len(invocations) == 1


def test_empty_output_is_retried(monkeypatch):
    results = iter(
        ({"output": "", "error": None}, {"output": "recovered", "error": None})
    )
    monkeypatch.setattr(subject_port.subprocess, "run", lambda cmd, **kw: None)
    monkeypatch.setattr(subject_port, "resolve_node_runtime", lambda: "/bin/runtime")
    monkeypatch.setattr(subject_port.time, "sleep", lambda *args: None)
    monkeypatch.setattr(subject_port, "read_result_file", lambda path: next(results))

    output, invoked = invoke_subject("opencode", prompt="q")

    assert invoked is True
    assert output == "recovered"


def test_timeout_surfaces_a_transient_failure_then_retries(monkeypatch):
    from subprocess import TimeoutExpired

    attempts = []
    monkeypatch.setattr(subject_port.time, "sleep", lambda *args: None)
    monkeypatch.setattr(subject_port, "resolve_node_runtime", lambda: "/bin/runtime")

    def fake_run(cmd, **kwargs):
        attempts.append(True)
        if len(attempts) == 1:
            raise TimeoutExpired(["/bin/runtime"], 5)
        return _CompletedProcess()

    monkeypatch.setattr(subject_port.subprocess, "run", fake_run)
    monkeypatch.setattr(
        subject_port,
        "read_result_file",
        lambda path: {"output": "recovered", "error": None},
    )

    output, invoked = invoke_subject("claude", prompt="q", timeout=5)

    assert invoked is True
    assert output == "recovered"
    assert len(attempts) == 2


def test_each_retry_starts_without_a_stale_result(monkeypatch, tmp_path):
    result_path = tmp_path / "result.json"
    result_path.write_text('{"output": "stale", "error": null}', encoding="utf-8")
    observed_existence = []

    def fake_run(cmd, **kwargs):
        observed_existence.append(result_path.exists())

    monkeypatch.setattr(subject_port.subprocess, "run", fake_run)
    monkeypatch.setattr(subject_port, "resolve_node_runtime", lambda: "/bin/runtime")
    monkeypatch.setattr(
        subject_port.tempfile,
        "TemporaryDirectory",
        lambda **kw: nullcontext(str(tmp_path)),
    )
    monkeypatch.setattr(
        subject_port,
        "read_result_file",
        lambda path: {"output": "fresh", "error": None},
    )

    output, invoked = invoke_subject("claude", prompt="q")

    assert invoked is True
    assert output == "fresh"
    assert observed_existence == [False]


def test_invalid_result_file_is_reported(tmp_path):
    result_path = tmp_path / "result.json"
    result_path.write_text("", encoding="utf-8")

    result = subject_port.read_result_file(result_path)

    assert result["output"] is None
    assert "invalid result" in result["error"]
