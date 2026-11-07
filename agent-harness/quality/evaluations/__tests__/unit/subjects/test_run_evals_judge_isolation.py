import json
from pathlib import Path

from runner import run_evals_worktree_and_environment as evaluation_environment
from runner.execution import run_evals_subject_port as subject_port


class _CompletedProcess:
    returncode = 0
    stdout = ""
    stderr = ""


def test_a_judge_runs_isolated_in_an_empty_directory_outside_the_repository(
    monkeypatch,
):
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["invocation"] = json.loads(kwargs["input"])
        captured["cwd"] = kwargs["cwd"]
        captured["cwd_entries"] = list(Path(kwargs["cwd"]).iterdir())
        return _CompletedProcess()

    monkeypatch.setattr(subject_port.subprocess, "run", fake_run)
    monkeypatch.setattr(subject_port, "resolve_node_runtime", lambda: "/bin/runtime")
    monkeypatch.setattr(
        subject_port,
        "read_result_file",
        lambda path: {"output": "VERDICT: PASS", "error": None},
    )

    judge = subject_port.build_provider_invoker("codex")
    judge("grade this", model="gpt-6-luna", no_tools=True)

    assert captured["invocation"]["isolated_context"] is True
    assert captured["cwd"] != str(evaluation_environment.EVAL_WORKING_DIRECTORY)
    assert captured["cwd_entries"] == []
    assert not Path(captured["cwd"]).exists()
