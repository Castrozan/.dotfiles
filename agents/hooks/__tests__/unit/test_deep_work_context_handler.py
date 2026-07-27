import json
import os
import time

from flat_deploy_test_support import (
    flatten_into_single_runtime_directory,
    run_flattened_hook,
)
from hook_module_loader import import_hyphenated_hook_module

deep_work_context_handler = import_hyphenated_hook_module("deep_work_context_handler")

SECONDS_PER_HOUR = 3600


def write_workspace(deep_work_directory, task_name, body, hours_since_progress=0):
    task_directory = deep_work_directory / task_name
    task_directory.mkdir(parents=True)
    (task_directory / "context.md").write_text(body, encoding="utf-8")
    progress_file = task_directory / "progress.md"
    progress_file.write_text(f"progress for {task_name}\n", encoding="utf-8")
    if hours_since_progress:
        aged = time.time() - hours_since_progress * SECONDS_PER_HOUR
        os.utime(progress_file, (aged, aged))
    return task_directory


def handle_with_deep_work_directory(deep_work_directory, monkeypatch):
    monkeypatch.setenv(
        deep_work_context_handler.DEEP_WORK_DIRECTORY_ENVIRONMENT_VARIABLE,
        str(deep_work_directory),
    )
    return deep_work_context_handler.handle({})


def test_returns_nothing_when_no_workspace_exists(tmp_path, monkeypatch):
    assert handle_with_deep_work_directory(tmp_path / "empty", monkeypatch) is None


def test_names_an_active_workspace_without_injecting_its_body(tmp_path, monkeypatch):
    deep_work_directory = tmp_path / "deep-work"
    write_workspace(deep_work_directory, "alpha", "ALPHA_BODY_MARKER " * 500)

    injected = handle_with_deep_work_directory(
        deep_work_directory, monkeypatch
    ).additional_context

    assert "alpha" in injected
    assert "ALPHA_BODY_MARKER" not in injected


def test_reports_a_stale_workspace_separately_from_an_active_one(tmp_path, monkeypatch):
    deep_work_directory = tmp_path / "deep-work"
    write_workspace(deep_work_directory, "current", "body")
    write_workspace(deep_work_directory, "abandoned", "body", hours_since_progress=200)

    injected = handle_with_deep_work_directory(
        deep_work_directory, monkeypatch
    ).additional_context

    active_section, _, stale_section = injected.partition("STALE")
    assert "current" in active_section
    assert "abandoned" not in active_section
    assert "abandoned" in stale_section


def test_stays_small_enough_to_be_an_orientation_signal(tmp_path, monkeypatch):
    deep_work_directory = tmp_path / "deep-work"
    for index in range(21):
        write_workspace(deep_work_directory, f"task-{index}", "x" * 6000)

    injected = handle_with_deep_work_directory(
        deep_work_directory, monkeypatch
    ).additional_context

    assert len(injected) < 4000


def test_codex_session_start_names_the_workspace_and_claude_does_not(tmp_path):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(runtime_directory)
    deep_work_directory = tmp_path / "deep-work"
    write_workspace(deep_work_directory, "alpha", "ALPHA_BODY_MARKER")

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
    assert "alpha" in injected
    assert "ALPHA_BODY_MARKER" not in injected

    on_claude = run_flattened_hook(
        runtime_directory, "session-start-dispatcher.py", payload, environment
    )
    assert on_claude.returncode == 0
    assert "alpha" not in on_claude.stdout
