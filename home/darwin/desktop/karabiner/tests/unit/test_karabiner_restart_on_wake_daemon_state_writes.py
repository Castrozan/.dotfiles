import json
from unittest.mock import MagicMock


def test_kick_writes_kick_metadata_and_increments_total_counter(
    daemon_module_with_temporary_paths,
    monkeypatch,
    make_completed_process_with_exit_zero,
):
    daemon_module = daemon_module_with_temporary_paths
    monkeypatch.setattr(
        daemon_module.subprocess,
        "run",
        MagicMock(return_value=make_completed_process_with_exit_zero()),
    )
    daemon_module.kick_karabiner_user_agents_via_launchctl("wake")
    daemon_module.kick_karabiner_user_agents_via_launchctl("periodic_safety_net")
    final_health_state = daemon_module.read_current_health_state_from_file()
    assert final_health_state["kick_count_total"] == 2
    assert final_health_state["last_kick_reason"] == "periodic_safety_net"
    assert "last_kick_epoch" in final_health_state
    assert "last_kick_duration_seconds" in final_health_state


def test_wake_event_writes_wake_epoch_and_kicks(
    daemon_module_with_temporary_paths,
    monkeypatch,
    make_completed_process_with_exit_zero,
):
    daemon_module = daemon_module_with_temporary_paths
    monkeypatch.setattr(
        daemon_module.subprocess,
        "run",
        MagicMock(return_value=make_completed_process_with_exit_zero()),
    )
    daemon_module.record_wake_event_in_health_state_and_kick()
    final_health_state = daemon_module.read_current_health_state_from_file()
    assert "last_wake_epoch" in final_health_state
    assert final_health_state["last_kick_reason"] == "wake"


def test_periodic_safety_net_kick_uses_periodic_reason(
    daemon_module_with_temporary_paths,
    monkeypatch,
    make_completed_process_with_exit_zero,
):
    daemon_module = daemon_module_with_temporary_paths
    daemon_module.write_merged_health_state_updates_to_file(
        {"karabiner_cli_ipc_probe_succeeded": False}
    )
    monkeypatch.setattr(
        daemon_module.subprocess,
        "run",
        MagicMock(return_value=make_completed_process_with_exit_zero()),
    )
    daemon_module.run_periodic_safety_net_kick()
    final_health_state = daemon_module.read_current_health_state_from_file()
    assert final_health_state["last_kick_reason"] == "periodic_safety_net"


def test_health_state_writes_are_merged_not_overwritten(
    daemon_module_with_temporary_paths,
):
    daemon_module = daemon_module_with_temporary_paths
    daemon_module.write_merged_health_state_updates_to_file({"alpha": 1, "beta": 2})
    daemon_module.write_merged_health_state_updates_to_file({"beta": 99, "gamma": 3})
    final_health_state = daemon_module.read_current_health_state_from_file()
    assert final_health_state == {"alpha": 1, "beta": 99, "gamma": 3}


def test_structured_log_appends_one_json_line_per_event(
    daemon_module_with_temporary_paths,
):
    daemon_module = daemon_module_with_temporary_paths
    daemon_module.append_structured_event_log_line({"event": "first"})
    daemon_module.append_structured_event_log_line({"event": "second", "extra": 42})
    with open(daemon_module.DAEMON_STRUCTURED_EVENT_LOG_FILE_PATH, "r") as log_file:
        log_lines = log_file.readlines()
    assert len(log_lines) == 2
    first_event = json.loads(log_lines[0])
    second_event = json.loads(log_lines[1])
    assert first_event["event"] == "first"
    assert second_event["event"] == "second"
    assert second_event["extra"] == 42
    assert "epoch" in first_event
    assert "iso8601" in first_event
