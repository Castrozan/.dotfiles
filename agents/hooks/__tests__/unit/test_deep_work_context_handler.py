import json
import os

from flat_deploy_test_support import (
    flatten_into_single_runtime_directory,
    run_flattened_hook,
)
from hook_module_loader import import_hyphenated_hook_module

deep_work_context_handler = import_hyphenated_hook_module("deep_work_context_handler")


def write_deep_work_context(deep_work_directory, task_name, body):
    task_directory = deep_work_directory / task_name
    task_directory.mkdir(parents=True)
    (task_directory / "context.md").write_text(body, encoding="utf-8")


def test_returns_nothing_when_no_deep_work_is_active(tmp_path, monkeypatch):
    monkeypatch.setenv(
        deep_work_context_handler.DEEP_WORK_DIRECTORY_ENVIRONMENT_VARIABLE,
        str(tmp_path / "empty"),
    )
    assert deep_work_context_handler.handle({}) is None


def test_joins_every_active_deep_work_context(tmp_path, monkeypatch):
    deep_work_directory = tmp_path / "deep-work"
    write_deep_work_context(deep_work_directory, "alpha", "alpha context")
    write_deep_work_context(deep_work_directory, "beta", "beta context")
    monkeypatch.setenv(
        deep_work_context_handler.DEEP_WORK_DIRECTORY_ENVIRONMENT_VARIABLE,
        str(deep_work_directory),
    )

    result = deep_work_context_handler.handle({})
    assert "alpha context" in result.additional_context
    assert "beta context" in result.additional_context


def test_skips_an_empty_context_document(tmp_path, monkeypatch):
    deep_work_directory = tmp_path / "deep-work"
    write_deep_work_context(deep_work_directory, "blank", "   \n")
    monkeypatch.setenv(
        deep_work_context_handler.DEEP_WORK_DIRECTORY_ENVIRONMENT_VARIABLE,
        str(deep_work_directory),
    )
    assert deep_work_context_handler.handle({}) is None


def test_codex_session_start_injects_deep_work_context_and_claude_does_not(tmp_path):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(runtime_directory)
    deep_work_directory = tmp_path / "deep-work"
    write_deep_work_context(deep_work_directory, "alpha", "alpha context")

    environment = {
        **os.environ,
        "HOME": str(tmp_path),
        "TMPDIR": str(tmp_path),
        deep_work_context_handler.DEEP_WORK_DIRECTORY_ENVIRONMENT_VARIABLE: str(
            deep_work_directory
        ),
    }
    payload = {"hook_event_name": "SessionStart", "source": "startup"}

    on_codex = run_flattened_hook(
        runtime_directory,
        "session-start-dispatcher.py",
        payload,
        environment,
        ("--surface=codex",),
    )
    assert on_codex.returncode == 0
    injected = json.loads(on_codex.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "alpha context" in injected

    on_claude = run_flattened_hook(
        runtime_directory, "session-start-dispatcher.py", payload, environment
    )
    assert on_claude.returncode == 0
    assert "alpha context" not in on_claude.stdout
