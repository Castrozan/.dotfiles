from clawde_service_test_helpers import (
    FakeCompletedProcess,
    fake_tmux_with_window_inventory,
    load_service_module,
)

service_module = load_service_module()


def _patch_no_running_wrappers(monkeypatch):
    monkeypatch.setattr(
        service_module.agent_wrapper_reconcile,
        "find_session_agent_wrapper_processes",
        lambda _session_name: [],
    )


def test_reconcile_recreates_a_session_that_died_after_startup(monkeypatch):
    _patch_no_running_wrappers(monkeypatch)
    live_session_names = {"ai-first-initiative", "esfinge"}
    issued_new_session_names = []

    def fake_run_tmux_command(*arguments):
        subcommand = arguments[0]
        if subcommand == "has-session":
            requested_session_name = arguments[2]
            return FakeCompletedProcess(
                0 if requested_session_name in live_session_names else 1
            )
        if subcommand == "new-session":
            created_session_name = arguments[3]
            issued_new_session_names.append(created_session_name)
            live_session_names.add(created_session_name)
            return FakeCompletedProcess(0)
        if subcommand == "list-windows":
            return FakeCompletedProcess(0, stdout="silver\n")
        return FakeCompletedProcess(0)

    monkeypatch.setattr(service_module, "run_tmux_command", fake_run_tmux_command)
    monkeypatch.setattr(service_module.time, "sleep", lambda _seconds: None)

    specification = {
        "sessions": [
            {
                "name": "ai-first-initiative",
                "agents": [{"name": "ai-first-initiative", "wrapper_command": "true"}],
            },
            {
                "name": "clawde",
                "agents": [{"name": "first-agent", "wrapper_command": "true"}],
            },
            {
                "name": "esfinge",
                "agents": [{"name": "esfinge", "wrapper_command": "true"}],
            },
        ]
    }

    service_module.ensure_all_agent_windows(specification)

    assert issued_new_session_names == ["clawde"], (
        "reconcile must recreate the dead 'clawde' session and only it"
    )


def test_each_newly_created_agent_window_is_staggered(monkeypatch):
    _patch_no_running_wrappers(monkeypatch)
    monkeypatch.setattr(
        service_module,
        "run_tmux_command",
        fake_tmux_with_window_inventory(set(), {}),
    )
    stagger_sleeps = []
    monkeypatch.setattr(
        service_module.time, "sleep", lambda seconds: stagger_sleeps.append(seconds)
    )

    specification = {
        "sessions": [
            {
                "name": "clawde",
                "agents": [
                    {"name": "first-agent", "wrapper_command": "true"},
                    {"name": "second-agent", "wrapper_command": "true"},
                    {"name": "third-agent", "wrapper_command": "true"},
                    {"name": "fourth-agent", "wrapper_command": "true"},
                ],
            }
        ]
    }

    service_module.ensure_all_agent_windows(specification)

    assert stagger_sleeps == [service_module.AGENT_STARTUP_STAGGER_SECONDS] * 4, (
        "every newly created agent window must be staggered so the agents do not "
        "spawn the shared Discord bun plugin MCP server concurrently and race on "
        "linking dependencies"
    )


def test_steady_state_reconcile_does_not_stagger_existing_windows(monkeypatch):
    _patch_no_running_wrappers(monkeypatch)
    monkeypatch.setattr(
        service_module,
        "run_tmux_command",
        fake_tmux_with_window_inventory(
            {"clawde"},
            {"clawde": {"first-agent", "second-agent", "third-agent", "fourth-agent"}},
        ),
    )
    stagger_sleeps = []
    monkeypatch.setattr(
        service_module.time, "sleep", lambda seconds: stagger_sleeps.append(seconds)
    )

    specification = {
        "sessions": [
            {
                "name": "clawde",
                "agents": [
                    {"name": "first-agent", "wrapper_command": "true"},
                    {"name": "second-agent", "wrapper_command": "true"},
                    {"name": "third-agent", "wrapper_command": "true"},
                    {"name": "fourth-agent", "wrapper_command": "true"},
                ],
            }
        ]
    }

    service_module.ensure_all_agent_windows(specification)

    assert stagger_sleeps == [], (
        "a reconcile pass where every agent window already exists must not sleep"
    )


def test_supervisor_reconciles_every_tick_instead_of_only_checking_existence(
    monkeypatch,
):
    reconcile_invocation_count = {"value": 0}

    def fake_ensure_all_agent_windows(_specification):
        reconcile_invocation_count["value"] += 1

    monkeypatch.setattr(
        service_module, "ensure_all_agent_windows", fake_ensure_all_agent_windows
    )

    class _StopReconcileLoop(Exception):
        pass

    def fake_sleep(_seconds):
        if reconcile_invocation_count["value"] >= 3:
            raise _StopReconcileLoop

    monkeypatch.setattr(service_module.time, "sleep", fake_sleep)

    specification = {"sessions": [{"name": "clawde", "agents": []}]}

    try:
        service_module.reconcile_sessions_forever(
            specification, poll_interval_seconds=0
        )
    except _StopReconcileLoop:
        pass

    assert reconcile_invocation_count["value"] >= 3, (
        "the supervisor must re-ensure all declared sessions every tick so a session "
        "that dies after startup gets recreated; the old loop only checked existence"
    )
