from unittest.mock import MagicMock


def run_full_health_probe_with_fake_completions(
    daemon_module, monkeypatch, call_route_map, route_subprocess_run_to_fake_completions
):
    subprocess_run_mock = MagicMock(
        side_effect=route_subprocess_run_to_fake_completions(call_route_map)
    )
    monkeypatch.setattr(daemon_module.subprocess, "run", subprocess_run_mock)
    monkeypatch.setattr(
        daemon_module,
        "get_file_modification_epoch_seconds_or_none",
        lambda _file_path: 1234567890.5,
    )
    daemon_module.run_full_health_probe_and_kick_if_ipc_probe_failed()
    return subprocess_run_mock


def registrar_subcommands_invoked(subprocess_run_mock):
    return [
        call.args[0][1]
        for call in subprocess_run_mock.call_args_list
        if "Non-Privileged Agents" in call.args[0][0]
    ]


def test_full_health_probe_reregisters_core_agents_when_karabiner_quit_unregistered_them(
    daemon_module_with_temporary_paths,
    monkeypatch,
    make_completed_process_with_exit_zero,
    make_completed_process_with_exit_one,
    route_subprocess_run_to_fake_completions,
):
    daemon_module = daemon_module_with_temporary_paths
    subprocess_run_mock = run_full_health_probe_with_fake_completions(
        daemon_module,
        monkeypatch,
        {
            "pgrep": make_completed_process_with_exit_one(),
            "karabiner_cli_profile": make_completed_process_with_exit_zero("Default\n"),
            "karabiner_cli_devices": make_completed_process_with_exit_zero(""),
            "core_agents_enabled": make_completed_process_with_exit_zero(
                "There are services that are not enabled\n"
            ),
        },
        route_subprocess_run_to_fake_completions,
    )
    assert registrar_subcommands_invoked(subprocess_run_mock) == [
        "core-agents-enabled",
        "register-core-agents",
    ]
    final_health_state = daemon_module.read_current_health_state_from_file()
    assert final_health_state["core_agents_registration_count_total"] == 1
    assert "last_core_agents_registration_epoch" in final_health_state


def test_full_health_probe_leaves_registered_core_agents_alone(
    daemon_module_with_temporary_paths,
    monkeypatch,
    make_completed_process_with_exit_zero,
    make_completed_process_with_exit_one,
    route_subprocess_run_to_fake_completions,
):
    daemon_module = daemon_module_with_temporary_paths
    subprocess_run_mock = run_full_health_probe_with_fake_completions(
        daemon_module,
        monkeypatch,
        {
            "pgrep": make_completed_process_with_exit_one(),
            "karabiner_cli_profile": make_completed_process_with_exit_zero("Default\n"),
            "karabiner_cli_devices": make_completed_process_with_exit_zero(""),
        },
        route_subprocess_run_to_fake_completions,
    )
    assert registrar_subcommands_invoked(subprocess_run_mock) == ["core-agents-enabled"]
    final_health_state = daemon_module.read_current_health_state_from_file()
    assert "core_agents_registration_count_total" not in final_health_state


def test_full_health_probe_skips_registration_check_while_console_user_server_runs(
    daemon_module_with_temporary_paths,
    monkeypatch,
    make_completed_process_with_exit_zero,
    karabiner_cli_list_connected_devices_json_with_one_keyboard,
    route_subprocess_run_to_fake_completions,
):
    daemon_module = daemon_module_with_temporary_paths
    subprocess_run_mock = run_full_health_probe_with_fake_completions(
        daemon_module,
        monkeypatch,
        {
            "pgrep": make_completed_process_with_exit_zero(),
            "karabiner_cli_profile": make_completed_process_with_exit_zero("Default\n"),
            "karabiner_cli_devices": make_completed_process_with_exit_zero(
                karabiner_cli_list_connected_devices_json_with_one_keyboard
            ),
        },
        route_subprocess_run_to_fake_completions,
    )
    assert registrar_subcommands_invoked(subprocess_run_mock) == []


def test_full_health_probe_survives_missing_core_agents_registrar(
    daemon_module_with_temporary_paths,
    monkeypatch,
    make_completed_process_with_exit_zero,
    make_completed_process_with_exit_one,
    route_subprocess_run_to_fake_completions,
):
    daemon_module = daemon_module_with_temporary_paths
    route_to_fake_completions = route_subprocess_run_to_fake_completions(
        {
            "pgrep": make_completed_process_with_exit_one(),
            "karabiner_cli_profile": make_completed_process_with_exit_zero("Default\n"),
            "karabiner_cli_devices": make_completed_process_with_exit_zero(""),
        }
    )

    def fake_run_without_registrar(command_line_arguments, **kwargs):
        if "Non-Privileged Agents" in command_line_arguments[0]:
            raise FileNotFoundError(command_line_arguments[0])
        return route_to_fake_completions(command_line_arguments, **kwargs)

    monkeypatch.setattr(
        daemon_module.subprocess,
        "run",
        MagicMock(side_effect=fake_run_without_registrar),
    )
    monkeypatch.setattr(
        daemon_module,
        "get_file_modification_epoch_seconds_or_none",
        lambda _file_path: 1234567890.5,
    )
    daemon_module.run_full_health_probe_and_kick_if_ipc_probe_failed()
    final_health_state = daemon_module.read_current_health_state_from_file()
    assert "core_agents_registration_count_total" not in final_health_state
