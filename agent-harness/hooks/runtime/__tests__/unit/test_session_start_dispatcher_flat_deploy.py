import json

from flat_deploy_test_support import (
    CLAWDE_BACKGROUND_AGENT_ENV_MARKER,
    INTERACTIVE_ENV_VAR,
    flatten_into_single_runtime_directory,
    run_flattened_hook,
)


def test_session_start_dispatcher_injects_no_servant_context(tmp_path):
    """The Servant reaches a session through the launch wrapper's appended system
    prompt, never through hook context, so the dispatcher must stay silent about
    it even though a session always has one."""
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(runtime_directory)

    injected = run_flattened_hook(
        runtime_directory,
        "session-start-dispatcher.py",
        {
            "hook_event_name": "SessionStart",
            "session_id": "servant-flat-probe",
            "cwd": str(tmp_path),
        },
        {
            "HOME": str(tmp_path),
            "TMPDIR": str(tmp_path),
            INTERACTIVE_ENV_VAR: "/nix/store/preferences.md",
        },
    )
    assert injected.returncode == 0
    payload = json.loads(injected.stdout)
    assert payload["continue"] is True
    injected_context = payload.get("hookSpecificOutput", {}).get(
        "additionalContext", ""
    )
    assert "SERVANT" not in injected_context


def test_session_start_dispatcher_stays_silent_for_clawde_agent_after_flat_deploy(
    tmp_path,
):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(runtime_directory)

    silent = run_flattened_hook(
        runtime_directory,
        "session-start-dispatcher.py",
        {
            "hook_event_name": "SessionStart",
            "session_id": "servant-flat-clawde-probe",
            "cwd": str(tmp_path),
        },
        {
            "HOME": str(tmp_path),
            "TMPDIR": str(tmp_path),
            INTERACTIVE_ENV_VAR: "/nix/store/preferences.md",
            CLAWDE_BACKGROUND_AGENT_ENV_MARKER: "steward",
        },
    )
    assert silent.returncode == 0
    assert "SERVANT" not in silent.stdout
