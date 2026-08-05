import subprocess


def test_karabiner_cli_ipc_probe_returns_success_with_profile_and_keyboard_count(
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
    monkeypatch.setattr(daemon_module.subprocess, "run", fake_run)
    probe_outcome = daemon_module.probe_karabiner_cli_ipc_and_return_outcome()
    assert probe_outcome["succeeded"] is True
    assert probe_outcome["failure_reason"] is None
    assert probe_outcome["profile_name"] == "Default"
    assert probe_outcome["grabbed_keyboard_device_count"] == 1


def test_karabiner_cli_ipc_probe_returns_failure_on_timeout(
    daemon_module_with_temporary_paths, monkeypatch
):
    daemon_module = daemon_module_with_temporary_paths

    def raising_subprocess_run(command_line_arguments, **_kwargs):
        raise subprocess.TimeoutExpired(command_line_arguments, timeout=2)

    monkeypatch.setattr(daemon_module.subprocess, "run", raising_subprocess_run)
    probe_outcome = daemon_module.probe_karabiner_cli_ipc_and_return_outcome()
    assert probe_outcome["succeeded"] is False
    assert "timed out" in probe_outcome["failure_reason"]


def test_karabiner_cli_ipc_probe_returns_failure_on_nonzero_exit(
    daemon_module_with_temporary_paths,
    monkeypatch,
    make_completed_process_with_exit_zero,
    make_completed_process_with_exit_one,
    route_subprocess_run_to_fake_completions,
):
    daemon_module = daemon_module_with_temporary_paths
    fake_run = route_subprocess_run_to_fake_completions(
        {
            "pgrep": make_completed_process_with_exit_zero(),
            "karabiner_cli_profile": make_completed_process_with_exit_one(""),
            "karabiner_cli_devices": make_completed_process_with_exit_zero("[]"),
        }
    )
    monkeypatch.setattr(daemon_module.subprocess, "run", fake_run)
    probe_outcome = daemon_module.probe_karabiner_cli_ipc_and_return_outcome()
    assert probe_outcome["succeeded"] is False
    assert "show-current-profile-name exit 1" in probe_outcome["failure_reason"]


def test_karabiner_cli_ipc_probe_returns_failure_when_binary_missing(
    daemon_module_with_temporary_paths, monkeypatch
):
    daemon_module = daemon_module_with_temporary_paths

    def raising_subprocess_run(_command_line_arguments, **_kwargs):
        raise FileNotFoundError("karabiner_cli")

    monkeypatch.setattr(daemon_module.subprocess, "run", raising_subprocess_run)
    probe_outcome = daemon_module.probe_karabiner_cli_ipc_and_return_outcome()
    assert probe_outcome["succeeded"] is False
    assert "karabiner_cli binary not found" in probe_outcome["failure_reason"]
