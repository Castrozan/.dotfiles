import json

from flat_deploy_test_support import (
    CLAWDE_BACKGROUND_AGENT_ENV_MARKER,
    INTERACTIVE_ENV_VAR,
    flatten_into_single_runtime_directory,
    run_flattened_hook,
)


def _injected_context(
    tmp_path, session_id, extra_environment=None, working_directory=None
):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir(parents=True, exist_ok=True)
    flatten_into_single_runtime_directory(runtime_directory)

    injected = run_flattened_hook(
        runtime_directory,
        "session-start-dispatcher.py",
        {
            "hook_event_name": "SessionStart",
            "session_id": session_id,
            "cwd": str(tmp_path),
        },
        {
            "HOME": str(tmp_path),
            "TMPDIR": str(tmp_path),
            INTERACTIVE_ENV_VAR: "/nix/store/preferences.md",
            **(extra_environment or {}),
        },
        working_directory=working_directory,
    )
    assert injected.returncode == 0, injected.stderr
    payload = json.loads(injected.stdout)
    assert payload["continue"] is True
    return payload.get("hookSpecificOutput", {}).get("additionalContext", "")


def test_session_start_dispatcher_names_the_servant_after_flat_deploy(tmp_path):
    """The Servant reaches the session as a value here and as a rule in the appended
    system prompt, so the flat deploy has to reach the servants domain to name one."""
    assert "Servant: " in _injected_context(tmp_path, "servant-flat-probe")


def test_a_repeated_session_id_names_the_same_servant(tmp_path):
    """The whole resume story. Nothing is persisted between launches, so a resumed
    conversation keeps its Servant only because the harness hands the hook back the
    same session id and the draw is a pure function of it."""
    first = _injected_context(tmp_path / "first", "servant-resume-probe")
    second = _injected_context(tmp_path / "second", "servant-resume-probe")
    assert "Servant: " in first
    assert first == second


def test_a_different_session_id_can_name_a_different_servant(tmp_path):
    drawn = {
        _injected_context(tmp_path / f"session-{index}", f"servant-spread-{index}")
        for index in range(8)
    }
    assert len(drawn) > 1


def test_session_start_dispatcher_stays_silent_for_clawde_agent_after_flat_deploy(
    tmp_path,
):
    """A clawde agent already carries its own name and personality, so it must never
    be handed a Servant that would compete with them."""
    injected_context = _injected_context(
        tmp_path,
        "servant-flat-clawde-probe",
        {CLAWDE_BACKGROUND_AGENT_ENV_MARKER: "steward"},
    )
    assert "Servant: " not in injected_context


def test_session_start_dispatcher_stays_silent_for_an_unmarked_agent_workspace(
    tmp_path,
):
    agent_workspace = tmp_path / "clawde" / "monster"
    agent_workspace.mkdir(parents=True)

    injected_context = _injected_context(
        tmp_path,
        "servant-flat-workspace-probe",
        working_directory=agent_workspace,
    )
    assert "Servant: " not in injected_context
