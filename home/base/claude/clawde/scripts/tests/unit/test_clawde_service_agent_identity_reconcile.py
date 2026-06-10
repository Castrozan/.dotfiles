from clawde_service_test_helpers import FakeCompletedProcess, load_service_module

service_module = load_service_module()


def _record_reconcile_effects(monkeypatch, list_windows_stdout, running_wrappers):
    issued_new_windows = []
    terminated_process_ids = []

    def fake_run_tmux_command(*arguments):
        subcommand = arguments[0]
        if subcommand == "has-session":
            return FakeCompletedProcess(0)
        if subcommand == "list-windows":
            return FakeCompletedProcess(0, stdout=list_windows_stdout)
        if subcommand == "new-window":
            issued_new_windows.append(arguments[4])
            return FakeCompletedProcess(0)
        return FakeCompletedProcess(0)

    monkeypatch.setattr(service_module, "run_tmux_command", fake_run_tmux_command)
    monkeypatch.setattr(service_module.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        service_module.agent_wrapper_reconcile,
        "find_session_agent_wrapper_processes",
        lambda _session_name: list(running_wrappers),
    )
    monkeypatch.setattr(
        service_module.agent_wrapper_reconcile,
        "terminate_agent_wrapper_process",
        terminated_process_ids.append,
    )
    monkeypatch.setattr(
        service_module.agent_wrapper_reconcile,
        "find_session_window_panes",
        lambda _session_name: [],
    )
    monkeypatch.setattr(
        service_module.agent_wrapper_reconcile,
        "rename_window",
        lambda _window_id, _window_name: None,
    )
    return issued_new_windows, terminated_process_ids


def _single_session_specification(agent_names):
    return {
        "sessions": [
            {
                "name": "clawde",
                "agents": [
                    {"name": name, "wrapper_command": "true"} for name in agent_names
                ],
            }
        ]
    }


def test_skips_creation_when_wrapper_already_runs_in_a_renamed_window(monkeypatch):
    issued_new_windows, terminated_process_ids = _record_reconcile_effects(
        monkeypatch,
        list_windows_stdout="betha-pm\njenny\nsilver\n",
        running_wrappers=[{"process_id": 4056, "agent_name": "steward"}],
    )

    service_module.ensure_all_agent_windows(
        _single_session_specification(["betha-pm", "jenny", "steward"])
    )

    assert "steward" not in issued_new_windows, (
        "a second steward window must not be created while a steward wrapper is already "
        "running, even though that wrapper lives in a window named 'silver' not 'steward'"
    )
    assert terminated_process_ids == [], (
        "the single in-spec steward wrapper must not be terminated"
    )


def test_terminates_extra_duplicate_wrappers_keeping_the_oldest(monkeypatch):
    issued_new_windows, terminated_process_ids = _record_reconcile_effects(
        monkeypatch,
        list_windows_stdout="silver\nsteward\n",
        running_wrappers=[
            {"process_id": 4056, "agent_name": "steward"},
            {"process_id": 6552, "agent_name": "steward"},
        ],
    )

    service_module.ensure_all_agent_windows(_single_session_specification(["steward"]))

    assert terminated_process_ids == [6552], (
        "with two steward wrappers alive the reconciler must terminate the extra one "
        "(highest pid) and keep exactly one"
    )
    assert "steward" not in issued_new_windows, (
        "no new steward window may be created while a steward wrapper survives"
    )


def test_terminates_orphan_wrapper_whose_agent_is_not_in_the_spec(monkeypatch):
    issued_new_windows, terminated_process_ids = _record_reconcile_effects(
        monkeypatch,
        list_windows_stdout="silver\n",
        running_wrappers=[{"process_id": 333, "agent_name": "silver"}],
    )

    service_module.ensure_all_agent_windows(_single_session_specification(["steward"]))

    assert terminated_process_ids == [333], (
        "a wrapper whose agent-name is not in the session spec is an orphan from a "
        "removed agent and must be terminated"
    )
    assert "steward" in issued_new_windows, (
        "the in-spec steward has no live wrapper, so its window must be created"
    )


def test_creates_window_when_no_wrapper_is_running(monkeypatch):
    issued_new_windows, terminated_process_ids = _record_reconcile_effects(
        monkeypatch,
        list_windows_stdout="",
        running_wrappers=[],
    )

    service_module.ensure_all_agent_windows(_single_session_specification(["steward"]))

    assert issued_new_windows == ["steward"]
    assert terminated_process_ids == []


def test_find_wrapper_processes_filters_by_session_and_parses_agent_name(monkeypatch):
    command_lines_by_process_id = {
        111: "python3 /n/agent-wrapper/wrapper.py --agent-name steward "
        "--config-file /c/steward.json",
        222: "python3 /n/agent-wrapper/wrapper.py --agent-name esfinge "
        "--config-file /c/esfinge.json",
        333: "python3 /n/agent-wrapper/wrapper.py --agent-name jenny "
        "--config-file /c/jenny.json",
    }
    tmux_session_by_config_file_path = {
        "/c/steward.json": "clawde",
        "/c/esfinge.json": "esfinge",
        "/c/jenny.json": "clawde",
    }

    def fake_subprocess_run(arguments, capture_output, text):
        if arguments[0] == "pgrep":
            return FakeCompletedProcess(0, stdout="111\n222\n333\n")
        process_id = int(arguments[arguments.index("-p") + 1])
        return FakeCompletedProcess(
            0, stdout=command_lines_by_process_id[process_id] + "\n"
        )

    monkeypatch.setattr(
        service_module.agent_wrapper_reconcile.subprocess, "run", fake_subprocess_run
    )
    monkeypatch.setattr(
        service_module.agent_wrapper_reconcile,
        "read_tmux_session_from_launch_config",
        lambda config_file_path: tmux_session_by_config_file_path[config_file_path],
    )

    discovered = (
        service_module.agent_wrapper_reconcile.find_session_agent_wrapper_processes(
            "clawde"
        )
    )

    assert discovered == [
        {"process_id": 111, "agent_name": "steward"},
        {"process_id": 333, "agent_name": "jenny"},
    ], (
        "discovery must return only wrappers whose --config-file declares tmux_session "
        "'clawde', so reconciling one session never terminates another session's agents"
    )
