import json
from unittest.mock import MagicMock


def _count_launchctl_calls(subprocess_run_mock):
    return sum(
        1
        for call in subprocess_run_mock.call_args_list
        if "launchctl" in call.args[0][0]
    )


def _read_structured_event_names(daemon_module):
    with open(daemon_module.DAEMON_STRUCTURED_EVENT_LOG_FILE_PATH, "r") as log_file:
        return [json.loads(log_line)["event"] for log_line in log_file]


def test_periodic_safety_net_kick_is_suppressed_when_health_state_is_healthy(
    daemon_module_with_temporary_paths,
    monkeypatch,
    make_completed_process_with_exit_zero,
):
    daemon_module = daemon_module_with_temporary_paths
    daemon_module.write_merged_health_state_updates_to_file(
        {
            "karabiner_cli_ipc_probe_succeeded": True,
            "karabiner_console_user_server_process_running": True,
            "karabiner_core_service_process_running": True,
            "karabiner_grabbed_keyboard_device_count": 2,
        }
    )
    subprocess_run_mock = MagicMock(
        return_value=make_completed_process_with_exit_zero()
    )
    monkeypatch.setattr(daemon_module.subprocess, "run", subprocess_run_mock)
    daemon_module.run_periodic_safety_net_kick()
    assert _count_launchctl_calls(subprocess_run_mock) == 0
    final_health_state = daemon_module.read_current_health_state_from_file()
    assert "last_kick_epoch" not in final_health_state
    assert (
        "periodic_safety_net_kick_suppressed_healthy"
        in _read_structured_event_names(daemon_module)
    )


def test_periodic_safety_net_kick_is_suppressed_when_health_state_is_missing(
    daemon_module_with_temporary_paths,
    monkeypatch,
    make_completed_process_with_exit_zero,
):
    daemon_module = daemon_module_with_temporary_paths
    subprocess_run_mock = MagicMock(
        return_value=make_completed_process_with_exit_zero()
    )
    monkeypatch.setattr(daemon_module.subprocess, "run", subprocess_run_mock)
    daemon_module.run_periodic_safety_net_kick()
    assert _count_launchctl_calls(subprocess_run_mock) == 0
    assert "last_kick_epoch" not in daemon_module.read_current_health_state_from_file()


def test_periodic_safety_net_kick_fires_when_ipc_probe_last_failed(
    daemon_module_with_temporary_paths,
    monkeypatch,
    make_completed_process_with_exit_zero,
):
    daemon_module = daemon_module_with_temporary_paths
    daemon_module.write_merged_health_state_updates_to_file(
        {
            "karabiner_cli_ipc_probe_succeeded": False,
            "karabiner_console_user_server_process_running": True,
            "karabiner_core_service_process_running": True,
            "karabiner_grabbed_keyboard_device_count": 2,
        }
    )
    subprocess_run_mock = MagicMock(
        return_value=make_completed_process_with_exit_zero()
    )
    monkeypatch.setattr(daemon_module.subprocess, "run", subprocess_run_mock)
    daemon_module.run_periodic_safety_net_kick()
    assert _count_launchctl_calls(subprocess_run_mock) == 3
    final_health_state = daemon_module.read_current_health_state_from_file()
    assert (
        final_health_state["last_kick_reason"]
        == daemon_module.KICK_REASON_PERIODIC_SAFETY_NET
    )


def test_periodic_safety_net_kick_fires_when_keyboard_grab_is_lost(
    daemon_module_with_temporary_paths,
    monkeypatch,
    make_completed_process_with_exit_zero,
):
    daemon_module = daemon_module_with_temporary_paths
    daemon_module.write_merged_health_state_updates_to_file(
        {
            "karabiner_cli_ipc_probe_succeeded": True,
            "karabiner_console_user_server_process_running": True,
            "karabiner_core_service_process_running": True,
            "karabiner_grabbed_keyboard_device_count": 0,
        }
    )
    subprocess_run_mock = MagicMock(
        return_value=make_completed_process_with_exit_zero()
    )
    monkeypatch.setattr(daemon_module.subprocess, "run", subprocess_run_mock)
    daemon_module.run_periodic_safety_net_kick()
    assert _count_launchctl_calls(subprocess_run_mock) == 3
    final_health_state = daemon_module.read_current_health_state_from_file()
    assert (
        final_health_state["last_kick_reason"]
        == daemon_module.KICK_REASON_PERIODIC_SAFETY_NET
    )


def test_periodic_safety_net_kick_fires_when_core_service_process_is_down(
    daemon_module_with_temporary_paths,
    monkeypatch,
    make_completed_process_with_exit_zero,
):
    daemon_module = daemon_module_with_temporary_paths
    daemon_module.write_merged_health_state_updates_to_file(
        {
            "karabiner_cli_ipc_probe_succeeded": True,
            "karabiner_console_user_server_process_running": True,
            "karabiner_core_service_process_running": False,
            "karabiner_grabbed_keyboard_device_count": 2,
        }
    )
    subprocess_run_mock = MagicMock(
        return_value=make_completed_process_with_exit_zero()
    )
    monkeypatch.setattr(daemon_module.subprocess, "run", subprocess_run_mock)
    daemon_module.run_periodic_safety_net_kick()
    assert _count_launchctl_calls(subprocess_run_mock) == 3
