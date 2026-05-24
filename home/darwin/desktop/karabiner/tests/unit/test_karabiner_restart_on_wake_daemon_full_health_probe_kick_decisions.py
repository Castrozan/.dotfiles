from unittest.mock import MagicMock


def test_full_health_probe_records_state_and_does_not_kick_when_healthy(
    daemon_module_with_temporary_paths,
    monkeypatch,
    make_completed_process_with_exit_zero,
    karabiner_cli_list_connected_devices_json_with_one_keyboard,
    route_subprocess_run_to_fake_completions,
):
    daemon_module = daemon_module_with_temporary_paths
    fake_run = route_subprocess_run_to_fake_completions(
        {
            "pgrep": make_completed_process_with_exit_zero(),
            "karabiner_cli_profile": make_completed_process_with_exit_zero("Default\n"),
            "karabiner_cli_devices": make_completed_process_with_exit_zero(
                karabiner_cli_list_connected_devices_json_with_one_keyboard
            ),
        }
    )
    subprocess_run_mock = MagicMock(side_effect=fake_run)
    monkeypatch.setattr(daemon_module.subprocess, "run", subprocess_run_mock)
    monkeypatch.setattr(
        daemon_module,
        "get_file_modification_epoch_seconds_or_none",
        lambda _file_path: 1234567890.5,
    )
    daemon_module.run_full_health_probe_and_kick_if_ipc_probe_failed()
    final_health_state = daemon_module.read_current_health_state_from_file()
    assert final_health_state["karabiner_cli_ipc_probe_succeeded"] is True
    assert final_health_state["karabiner_current_profile_name"] == "Default"
    assert final_health_state["karabiner_grabbed_keyboard_device_count"] == 1
    assert "last_kick_epoch" not in final_health_state
    kickstart_call_count = sum(
        1
        for call in subprocess_run_mock.call_args_list
        if "launchctl" in call.args[0][0]
    )
    assert kickstart_call_count == 0


def test_full_health_probe_does_not_kick_when_kick_feature_flag_is_disabled(
    daemon_module_with_temporary_paths,
    monkeypatch,
    make_completed_process_with_exit_zero,
    make_completed_process_with_exit_one,
    route_subprocess_run_to_fake_completions,
):
    daemon_module = daemon_module_with_temporary_paths
    monkeypatch.setattr(
        daemon_module, "KARABINER_CLI_IPC_PROBE_FAILURE_KICK_IS_ENABLED", False
    )
    monkeypatch.setattr(
        daemon_module,
        "CONSECUTIVE_IPC_PROBE_FAILURES_REQUIRED_BEFORE_KICK",
        1,
    )
    fake_run = route_subprocess_run_to_fake_completions(
        {
            "pgrep": make_completed_process_with_exit_zero(),
            "karabiner_cli_profile": make_completed_process_with_exit_one(""),
            "karabiner_cli_devices": make_completed_process_with_exit_zero("[]"),
        }
    )
    subprocess_run_mock = MagicMock(side_effect=fake_run)
    monkeypatch.setattr(daemon_module.subprocess, "run", subprocess_run_mock)
    monkeypatch.setattr(
        daemon_module,
        "get_file_modification_epoch_seconds_or_none",
        lambda _file_path: 1234567890.5,
    )
    daemon_module.run_full_health_probe_and_kick_if_ipc_probe_failed()
    final_health_state = daemon_module.read_current_health_state_from_file()
    assert final_health_state["karabiner_cli_ipc_probe_succeeded"] is False
    assert final_health_state["karabiner_cli_ipc_probe_failure_count_total"] == 1
    assert final_health_state["consecutive_ipc_probe_failure_count"] == 1
    assert "last_kick_epoch" not in final_health_state


def test_full_health_probe_kicks_when_feature_flag_enabled_and_threshold_met(
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
        2,
    )
    monkeypatch.setattr(daemon_module, "MINIMUM_SECONDS_BETWEEN_REACTIVE_KICKS", 0.0)
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
    assert (
        "last_kick_epoch" not in daemon_module.read_current_health_state_from_file()
    ), "first failure must not kick yet"
    daemon_module.run_full_health_probe_and_kick_if_ipc_probe_failed()
    final_health_state = daemon_module.read_current_health_state_from_file()
    assert (
        final_health_state["last_kick_reason"]
        == daemon_module.KICK_REASON_KARABINER_CLI_IPC_PROBE_FAILURE
    )
    assert final_health_state["consecutive_ipc_probe_failure_count"] == 2
