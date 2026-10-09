import json

import pytest

from flat_deploy_test_support import (
    flatten_into_single_runtime_directory,
    run_flattened_hook,
)


def test_pre_tool_use_dispatcher_imports_shared_modules_after_flat_deploy(tmp_path):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(runtime_directory)

    blocked = run_flattened_hook(
        runtime_directory,
        "pre-tool-use-dispatcher.py",
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Skill",
            "tool_input": {"skill": "claude-api"},
            "cwd": str(tmp_path),
            "session_id": "flat-deploy-probe",
        },
        {"HOME": str(tmp_path), "TMPDIR": str(tmp_path)},
    )
    assert blocked.returncode == 0
    payload = json.loads(blocked.stdout)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_pre_tool_use_dispatcher_enforces_prohibited_words_through_the_fold(tmp_path):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(runtime_directory)
    prohibited_words_file = tmp_path / "prohibited-words.txt"
    prohibited_words_file.write_text("supersecretword\n")

    blocked = run_flattened_hook(
        runtime_directory,
        "pre-tool-use-dispatcher.py",
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "git commit -m 'add supersecretword'"},
            "cwd": str(tmp_path),
            "session_id": "flat-deploy-words-probe",
        },
        {
            "HOME": str(tmp_path),
            "TMPDIR": str(tmp_path),
            "PROHIBITED_WORDS_FILE": str(prohibited_words_file),
            "PROHIBITED_WORDS_ALLOWED": "",
        },
    )
    assert blocked.returncode == 0
    payload = json.loads(blocked.stdout)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert (
        "supersecretword" in payload["hookSpecificOutput"]["permissionDecisionReason"]
    )


@pytest.mark.parametrize("surface", ["claude", "codex", "opencode", "pi", "hermes"])
@pytest.mark.parametrize(
    "command, denied",
    [("pytest -q tests/test_example.py", False), ("pytest -q", True)],
)
def test_flattened_dispatcher_loads_pytest_collection_helpers(
    tmp_path, surface, command, denied
):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(runtime_directory)
    completed = run_flattened_hook(
        runtime_directory,
        "pre-tool-use-dispatcher.py",
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": str(tmp_path),
            "session_id": "flat-pytest-probe",
        },
        {"HOME": str(tmp_path), "TMPDIR": str(tmp_path)},
        extra_arguments=(f"--surface={surface}",),
    )
    assert completed.returncode == 0
    assert completed.stderr == ""
    output = json.loads(completed.stdout) if completed.stdout else {}
    assert "failed and was skipped" not in output.get("systemMessage", "")
    decision = output.get("hookSpecificOutput", {}).get("permissionDecision")
    assert (decision == "deny") is denied
