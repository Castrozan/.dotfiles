from unittest.mock import MagicMock


def test_full_health_probe_resets_consecutive_failure_counter_on_success(
    daemon_module_with_temporary_paths,
    monkeypatch,
    make_completed_process_with_exit_zero,
    karabiner_cli_list_connected_devices_json_with_one_keyboard,
    route_subprocess_run_to_fake_completions,
):
    daemon_module = daemon_module_with_temporary_paths
    daemon_module.write_merged_health_state_updates_to_file(
        {"consecutive_ipc_probe_failure_count": 5}
    )
    fake_run = route_subprocess_run_to_fake_completions(
        {
            "pgrep": make_completed_process_with_exit_zero(),
            "karabiner_cli_profile": make_completed_process_with_exit_zero("Default\n"),
            "karabiner_cli_devices": make_completed_process_with_exit_zero(
                karabiner_cli_list_connected_devices_json_with_one_keyboard
            ),
        }
    )
    monkeypatch.setattr(
        daemon_module.subprocess, "run", MagicMock(side_effect=fake_run)
    )
    monkeypatch.setattr(
        daemon_module,
        "get_file_modification_epoch_seconds_or_none",
        lambda _file_path: 1234567890.5,
    )
    daemon_module.run_full_health_probe_and_kick_if_ipc_probe_failed()
    final_health_state = daemon_module.read_current_health_state_from_file()
    assert final_health_state["consecutive_ipc_probe_failure_count"] == 0


def test_full_health_probe_respects_cooldown_between_reactive_kicks(
    daemon_module_with_temporary_paths,
    monkeypatch,
    make_completed_process_with_exit_zero,
    make_completed_process_with_exit_one,
    route_subprocess_run_to_fake_completions,
):
    daemon_module = daemon_module_with_temporary_paths
    monkeypatch.setattr(
        daemon_module, "KARABINER_CLI_IPC_PROBE_FAILURE_KICK_IS_ENABLED", True
    )
    monkeypatch.setattr(
        daemon_module,
        "CONSECUTIVE_IPC_PROBE_FAILURES_REQUIRED_BEFORE_KICK",
        1,
    )
    monkeypatch.setattr(daemon_module, "MINIMUM_SECONDS_BETWEEN_REACTIVE_KICKS", 3600.0)
    daemon_module.write_merged_health_state_updates_to_file(
        {"last_reactive_kick_epoch": daemon_module.current_epoch_seconds()}
    )
    fake_run = route_subprocess_run_to_fake_completions(
        {
            "pgrep": make_completed_process_with_exit_zero(),
            "karabiner_cli_profile": make_completed_process_with_exit_one(""),
            "karabiner_cli_devices": make_completed_process_with_exit_zero("[]"),
        }
    )
    monkeypatch.setattr(
        daemon_module.subprocess, "run", MagicMock(side_effect=fake_run)
    )
    monkeypatch.setattr(
        daemon_module,
        "get_file_modification_epoch_seconds_or_none",
        lambda _file_path: 1234567890.5,
    )
    daemon_module.run_full_health_probe_and_kick_if_ipc_probe_failed()
    final_health_state = daemon_module.read_current_health_state_from_file()
    assert "last_kick_epoch" not in final_health_state


def test_full_health_probe_does_not_kick_when_user_server_not_running(
    daemon_module_with_temporary_paths,
    monkeypatch,
    make_completed_process_with_exit_zero,
    make_completed_process_with_exit_one,
    route_subprocess_run_to_fake_completions,
):
    daemon_module = daemon_module_with_temporary_paths
    monkeypatch.setattr(
        daemon_module, "KARABINER_CLI_IPC_PROBE_FAILURE_KICK_IS_ENABLED", True
    )
    monkeypatch.setattr(
        daemon_module,
        "CONSECUTIVE_IPC_PROBE_FAILURES_REQUIRED_BEFORE_KICK",
        1,
    )
    monkeypatch.setattr(daemon_module, "MINIMUM_SECONDS_BETWEEN_REACTIVE_KICKS", 0.0)
    fake_run = route_subprocess_run_to_fake_completions(
        {
            "pgrep": make_completed_process_with_exit_one(),
            "karabiner_cli_profile": make_completed_process_with_exit_one(""),
            "karabiner_cli_devices": make_completed_process_with_exit_zero("[]"),
        }
    )
    monkeypatch.setattr(
        daemon_module.subprocess, "run", MagicMock(side_effect=fake_run)
    )
    monkeypatch.setattr(
        daemon_module,
        "get_file_modification_epoch_seconds_or_none",
        lambda _file_path: None,
    )
    daemon_module.run_full_health_probe_and_kick_if_ipc_probe_failed()
    final_health_state = daemon_module.read_current_health_state_from_file()
    assert "last_kick_epoch" not in final_health_state
