import importlib.util
import pathlib
import sys


def _load_service_module():
    module_path = (
        pathlib.Path(__file__).resolve().parent.parent.parent / "clawde-service.py"
    )
    module_spec = importlib.util.spec_from_file_location("clawde_service", module_path)
    module = importlib.util.module_from_spec(module_spec)
    sys.modules["clawde_service"] = module
    module_spec.loader.exec_module(module)
    return module


service_module = _load_service_module()


class _FakeCompletedProcess:
    def __init__(self, returncode, stdout=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = ""


def test_reconcile_recreates_a_session_that_died_after_startup(monkeypatch):
    live_session_names = {"ai-first-initiative", "esfinge"}
    issued_new_session_names = []

    def fake_run_tmux_command(*arguments):
        subcommand = arguments[0]
        if subcommand == "has-session":
            requested_session_name = arguments[2]
            return _FakeCompletedProcess(
                0 if requested_session_name in live_session_names else 1
            )
        if subcommand == "new-session":
            created_session_name = arguments[3]
            issued_new_session_names.append(created_session_name)
            live_session_names.add(created_session_name)
            return _FakeCompletedProcess(0)
        if subcommand == "list-windows":
            return _FakeCompletedProcess(0, stdout="silver\n")
        return _FakeCompletedProcess(0)

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


def _fake_tmux_with_window_inventory(live_session_names, windows_by_session):
    def fake_run_tmux_command(*arguments):
        subcommand = arguments[0]
        if subcommand == "has-session":
            return _FakeCompletedProcess(0 if arguments[2] in live_session_names else 1)
        if subcommand == "new-session":
            session_name = arguments[3]
            live_session_names.add(session_name)
            windows_by_session.setdefault(session_name, set()).add(arguments[5])
            return _FakeCompletedProcess(0)
        if subcommand == "list-windows":
            return _FakeCompletedProcess(
                0, stdout="\n".join(windows_by_session.get(arguments[2], set()))
            )
        if subcommand == "new-window":
            windows_by_session.setdefault(arguments[2], set()).add(arguments[4])
            return _FakeCompletedProcess(0)
        return _FakeCompletedProcess(0)

    return fake_run_tmux_command


def test_each_newly_created_agent_window_is_staggered(monkeypatch):
    monkeypatch.setattr(
        service_module,
        "run_tmux_command",
        _fake_tmux_with_window_inventory(set(), {}),
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
    monkeypatch.setattr(
        service_module,
        "run_tmux_command",
        _fake_tmux_with_window_inventory(
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
