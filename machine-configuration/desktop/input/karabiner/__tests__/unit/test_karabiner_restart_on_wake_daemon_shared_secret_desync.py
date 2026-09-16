from unittest.mock import MagicMock


def write_console_user_server_log(temporary_daemon_state_paths, log_text):
    with open(
        temporary_daemon_state_paths["console_user_server_log_file_path"], "w"
    ) as console_user_server_log_file:
        console_user_server_log_file.write(log_text)


def test_invalid_shared_secret_count_is_zero_when_log_file_is_absent(
    daemon_module_with_temporary_paths,
):
    daemon_module = daemon_module_with_temporary_paths
    assert (
        daemon_module.count_invalid_shared_secret_errors_since_last_core_service_connect()
        == 0
    )


def test_invalid_shared_secret_count_only_counts_errors_after_most_recent_connect(
    daemon_module_with_temporary_paths, temporary_daemon_state_paths
):
    daemon_module = daemon_module_with_temporary_paths
    write_console_user_server_log(
        temporary_daemon_state_paths,
        "[info] core_service_client is connected.\n"
        "[error] operation_type::frontmost_application_changed with invalid shared secret\n"
        "[info] core_service_client is connected.\n"
        "[error] operation_type::frontmost_application_changed with invalid shared secret\n"
        "[error] operation_type::core_service_daemon_state with invalid shared secret\n",
    )
    assert (
        daemon_module.count_invalid_shared_secret_errors_since_last_core_service_connect()
        == 2
    )


def test_invalid_shared_secret_count_is_zero_when_last_connect_is_clean(
    daemon_module_with_temporary_paths, temporary_daemon_state_paths
):
    daemon_module = daemon_module_with_temporary_paths
    write_console_user_server_log(
        temporary_daemon_state_paths,
        "[error] operation_type::frontmost_application_changed with invalid shared secret\n"
        "[info] core_service_client is connected.\n",
    )
    assert (
        daemon_module.count_invalid_shared_secret_errors_since_last_core_service_connect()
        == 0
    )


def test_full_health_probe_kicks_on_shared_secret_desync_while_ipc_probe_is_healthy(
    daemon_module_with_temporary_paths,
    temporary_daemon_state_paths,
    monkeypatch,
    make_completed_process_with_exit_zero,
    karabiner_cli_list_connected_devices_json_with_one_keyboard,
    route_subprocess_run_to_fake_completions,
):
    daemon_module = daemon_module_with_temporary_paths
    monkeypatch.setattr(
        daemon_module, "KARABINER_CLI_IPC_PROBE_FAILURE_KICK_IS_ENABLED", True
    )
    monkeypatch.setattr(
        daemon_module,
        "CONSECUTIVE_SHARED_SECRET_DESYNC_PROBES_REQUIRED_BEFORE_KICK",
        1,
    )
    monkeypatch.setattr(daemon_module, "MINIMUM_SECONDS_BETWEEN_REACTIVE_KICKS", 0.0)
    write_console_user_server_log(
        temporary_daemon_state_paths,
        "[info] core_service_client is connected.\n"
        "[error] operation_type::frontmost_application_changed with invalid shared secret\n",
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
    assert final_health_state["karabiner_cli_ipc_probe_succeeded"] is True
    assert (
        final_health_state["last_kick_reason"]
        == daemon_module.KICK_REASON_SHARED_SECRET_DESYNC
    )
    assert (
        final_health_state[
            "karabiner_invalid_shared_secret_error_count_since_last_connect"
        ]
        == 1
    )


def test_full_health_probe_resets_desync_counter_when_secret_recovers(
    daemon_module_with_temporary_paths,
    temporary_daemon_state_paths,
    monkeypatch,
    make_completed_process_with_exit_zero,
    karabiner_cli_list_connected_devices_json_with_one_keyboard,
    route_subprocess_run_to_fake_completions,
):
    daemon_module = daemon_module_with_temporary_paths
    daemon_module.write_merged_health_state_updates_to_file(
        {"consecutive_shared_secret_desync_probe_count": 4}
    )
    write_console_user_server_log(
        temporary_daemon_state_paths,
        "[error] operation_type::frontmost_application_changed with invalid shared secret\n"
        "[info] core_service_client is connected.\n",
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
    assert final_health_state["consecutive_shared_secret_desync_probe_count"] == 0
    assert "last_kick_epoch" not in final_health_state


def test_kick_restarts_every_user_agent_in_restart_order(
    daemon_module_with_temporary_paths,
    monkeypatch,
    make_completed_process_with_exit_zero,
):
    daemon_module = daemon_module_with_temporary_paths
    subprocess_run_mock = MagicMock(
        return_value=make_completed_process_with_exit_zero()
    )
    monkeypatch.setattr(daemon_module.subprocess, "run", subprocess_run_mock)
    daemon_module.kick_karabiner_user_agents_via_launchctl("wake")
    kickstarted_launchd_labels_in_call_order = [
        call.args[0][3].rsplit("/", 1)[1]
        for call in subprocess_run_mock.call_args_list
        if "launchctl" in call.args[0][0]
    ]
    assert (
        kickstarted_launchd_labels_in_call_order
        == daemon_module.KARABINER_USER_AGENT_LAUNCHD_LABELS_TO_KICK_IN_RESTART_ORDER
    )
