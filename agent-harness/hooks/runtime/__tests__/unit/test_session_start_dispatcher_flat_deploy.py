import json

from flat_deploy_test_support import (
    CLAWDE_BACKGROUND_AGENT_ENV_MARKER,
    INTERACTIVE_ENV_VAR,
    flatten_into_single_runtime_directory,
    run_flattened_hook,
)


def test_session_start_dispatcher_injects_servant_context_after_flat_deploy(
    tmp_path, monkeypatch
):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(runtime_directory)
    monkeypatch.setenv("SERVANT_IDENTITY_STATE_DIRECTORY", str(tmp_path))

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
    assert "SERVANT:" in payload["hookSpecificOutput"]["additionalContext"]


def test_session_start_dispatcher_stays_silent_for_clawde_agent_after_flat_deploy(
    tmp_path, monkeypatch
):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(runtime_directory)
    monkeypatch.setenv("SERVANT_IDENTITY_STATE_DIRECTORY", str(tmp_path))

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
