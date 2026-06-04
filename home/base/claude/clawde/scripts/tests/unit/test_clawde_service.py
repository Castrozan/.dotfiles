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

    specification = {
        "sessions": [
            {
                "name": "ai-first-initiative",
                "agents": [{"name": "ai-first-initiative", "wrapper_command": "true"}],
            },
            {
                "name": "clawde",
                "agents": [{"name": "silver", "wrapper_command": "true"}],
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
