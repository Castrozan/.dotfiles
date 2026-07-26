import json

from flat_deploy_test_support import (
    PRE_TOOL_USE_DISPATCHER_RUNTIME_SOURCES,
    flatten_into_single_runtime_directory,
    run_flattened_hook,
)


def test_pre_tool_use_dispatcher_imports_shared_modules_after_flat_deploy(tmp_path):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(
        runtime_directory, PRE_TOOL_USE_DISPATCHER_RUNTIME_SOURCES
    )

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
