import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from runner.execution import run_evals_subject_port as subject_port
from runner import run_evals_worktree_and_environment as evaluation_environment

from instructions.instruction_surface_scanner import REPO_ROOT
from runner.baseline.run_evals_fingerprint import evaluation_runner_paths
from runner.run_evals_worktree_and_environment import (
    build_filtered_environment,
)

EVALUATION_PACKAGING_PATH = (
    REPO_ROOT
    / "agent-harness"
    / "quality"
    / "evaluations"
    / "agent-evaluations-home-manager.nix"
)


def test_isolation_strips_the_interactive_reply_shape_marker(monkeypatch):
    monkeypatch.setenv(
        "AGENT_INTERACTIVE_PREFERENCES_PATH", "/some/interactive/preferences.md"
    )
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setenv("PATH", "/usr/bin:/bin")

    filtered = build_filtered_environment()

    assert "AGENT_INTERACTIVE_PREFERENCES_PATH" not in filtered
    assert "CLAUDECODE" not in filtered
    assert filtered["PATH"] == "/usr/bin:/bin"


def test_the_measured_subjects_bypass_the_interactive_wrappers():
    packaging = EVALUATION_PACKAGING_PATH.read_text(encoding="utf-8")
    agent_eval_definition = packaging.split('writeShellScriptBin "agent-eval"', 1)[
        1
    ].split("'';", 1)[0]

    for harness in ("claude", "codex", "opencode"):
        assert f"config.{harness}.unwrappedPackage" in agent_eval_definition
    assert "AGENT_EVAL_CLAUDE_BINARY" in agent_eval_definition
    assert "AGENT_EVAL_CODEX_BINARY" in agent_eval_definition
    assert "config.claude.unwrappedPackage" in agent_eval_definition, (
        "the interactive wrapper appends the always-on reply-shape surface to every launch, "
        "including `-p --system-prompt` with the isolation variables stripped, so an eval that "
        "resolves the wrapped claude scores the live machine instead of the instruction paths "
        "its suite declares and its fingerprint records"
    )


def test_the_subject_launcher_is_fingerprinted():
    assert EVALUATION_PACKAGING_PATH in evaluation_runner_paths(REPO_ROOT), (
        "the packaging chooses which claude binary every sample runs against, and swapping the "
        "wrapped launcher for the unwrapped one moved this suite by seventeen points, so a "
        "baseline recorded under one launcher must not validate against another"
    )


def test_the_vendor_sdk_runtime_is_fingerprinted():
    runtime_paths = evaluation_runner_paths(REPO_ROOT)

    for relative_path in (
        "node-provider-runtime/package.nix",
        "node-provider-runtime/package.json",
        "node-provider-runtime/package-lock.json",
        "node-provider-runtime/provider-runtime.mjs",
    ):
        assert EVALUATION_PACKAGING_PATH.parent / relative_path in runtime_paths


def test_provider_calls_use_the_active_worktree_and_restore_after_failure(
    tmp_path, monkeypatch
):
    repository_path = tmp_path / "repository"
    repository_path.mkdir()
    subprocess.run(
        ["git", "init", str(repository_path)], check=True, capture_output=True
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Evaluation test",
            "-c",
            "user.email=evaluation@example.invalid",
            "-c",
            "core.hooksPath=/dev/null",
            "commit",
            "--allow-empty",
            "-m",
            "initial",
        ],
        cwd=repository_path,
        check=True,
        capture_output=True,
    )
    monkeypatch.setattr(evaluation_environment, "REPO_ROOT", repository_path)
    monkeypatch.setattr(
        evaluation_environment, "EVAL_WORKING_DIRECTORY", repository_path
    )
    monkeypatch.setattr(
        subject_port, "resolve_node_runtime", lambda: "evaluation-runtime"
    )
    original_run = subprocess.run
    invocations = []

    def capture_runtime(command, **arguments):
        if command != ["evaluation-runtime"]:
            return original_run(command, **arguments)
        invocation = json.loads(arguments["input"])
        invocations.append((invocation["working_directory"], arguments["cwd"]))
        Path(invocation["result_file"]).write_text(
            json.dumps({"output": "answer", "error": None})
        )

    monkeypatch.setattr(subprocess, "run", capture_runtime)
    with pytest.raises(RuntimeError, match="evaluation failed"):
        with evaluation_environment.temporary_eval_worktree() as worktree_path:
            assert worktree_path.parent == repository_path / ".worktrees"
            with ThreadPoolExecutor(max_workers=2) as executor:
                calls = [
                    executor.submit(
                        subject_port.invoke_subject, harness, prompt="question"
                    )
                    for harness in ("claude", "codex")
                ]
                assert all(call.result() == ("answer", True) for call in calls)
            subject_port.invoke_subject(
                "opencode", prompt="question", working_directory=repository_path
            )
            raise RuntimeError("evaluation failed")

    assert invocations == [
        (str(worktree_path), str(worktree_path)),
        (str(worktree_path), str(worktree_path)),
        (str(repository_path), str(repository_path)),
    ]
    assert evaluation_environment.EVAL_WORKING_DIRECTORY == repository_path
    assert not worktree_path.exists()
