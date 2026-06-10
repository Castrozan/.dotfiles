from clawde_service_test_helpers import load_service_module

reconcile_module = load_service_module().agent_wrapper_reconcile


def _capture_renames(monkeypatch, running_wrappers, window_panes):
    issued_renames = []
    monkeypatch.setattr(
        reconcile_module,
        "find_session_agent_wrapper_processes",
        lambda _session_name: list(running_wrappers),
    )
    monkeypatch.setattr(
        reconcile_module, "terminate_agent_wrapper_process", lambda _process_id: None
    )
    monkeypatch.setattr(
        reconcile_module,
        "find_session_window_panes",
        lambda _session_name: [dict(window_pane) for window_pane in window_panes],
    )
    monkeypatch.setattr(
        reconcile_module,
        "rename_window",
        lambda window_id, window_name: issued_renames.append((window_id, window_name)),
    )
    return issued_renames


def test_relabels_window_to_match_the_wrapper_running_in_its_pane(monkeypatch):
    issued_renames = _capture_renames(
        monkeypatch,
        running_wrappers=[{"process_id": 4056, "agent_name": "steward"}],
        window_panes=[{"window_id": "@7", "window_name": "silver", "pane_pid": 4056}],
    )

    reconcile_module.agent_names_with_running_wrapper_after_reconcile(
        "clawde", {"steward"}
    )

    assert issued_renames == [("@7", "steward")], (
        "the window whose pane runs the steward wrapper must be relabeled 'steward' even "
        "though it drifted to 'silver', so a heartbeat addressed to clawde:steward reaches "
        "the steward agent and not whoever else holds that window label"
    )


def test_leaves_a_window_already_matching_its_wrapper_untouched(monkeypatch):
    issued_renames = _capture_renames(
        monkeypatch,
        running_wrappers=[{"process_id": 4056, "agent_name": "steward"}],
        window_panes=[{"window_id": "@7", "window_name": "steward", "pane_pid": 4056}],
    )

    reconcile_module.agent_names_with_running_wrapper_after_reconcile(
        "clawde", {"steward"}
    )

    assert issued_renames == [], (
        "a window already labeled with the agent-name of the wrapper in its pane must "
        "not be renamed, so steady-state reconcile is a no-op"
    )


def test_relabels_only_the_surviving_duplicate_wrappers_window(monkeypatch):
    issued_renames = _capture_renames(
        monkeypatch,
        running_wrappers=[
            {"process_id": 4056, "agent_name": "steward"},
            {"process_id": 6552, "agent_name": "steward"},
        ],
        window_panes=[
            {"window_id": "@7", "window_name": "silver", "pane_pid": 4056},
            {"window_id": "@8", "window_name": "steward", "pane_pid": 6552},
        ],
    )

    reconcile_module.agent_names_with_running_wrapper_after_reconcile(
        "clawde", {"steward"}
    )

    assert issued_renames == [("@7", "steward")], (
        "only the surviving steward wrapper's window (kept pid 4056) is relabeled; the "
        "terminated duplicate's window (pid 6552) is left to close on its own"
    )


def test_ignores_windows_whose_pane_is_not_a_reconciled_wrapper(monkeypatch):
    issued_renames = _capture_renames(
        monkeypatch,
        running_wrappers=[{"process_id": 4056, "agent_name": "steward"}],
        window_panes=[{"window_id": "@9", "window_name": "scratch", "pane_pid": 999}],
    )

    reconcile_module.agent_names_with_running_wrapper_after_reconcile(
        "clawde", {"steward"}
    )

    assert issued_renames == [], (
        "a window whose pane pid is not one of the reconciled wrappers (a plain shell or "
        "an unrelated process) must never be renamed"
    )
