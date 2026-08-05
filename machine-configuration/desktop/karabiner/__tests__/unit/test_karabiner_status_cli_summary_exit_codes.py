import time


def test_summary_exits_zero_for_healthy_state(karabiner_status_cli_module):
    health_state = {
        "karabiner_core_service_process_running": True,
        "karabiner_console_user_server_process_running": True,
        "karabiner_cli_ipc_probe_succeeded": True,
        "last_health_probe_epoch": time.time(),
        "daemon_process_id": 123,
        "daemon_started_epoch": time.time() - 60,
    }
    _summary, exit_code = (
        karabiner_status_cli_module.format_health_state_as_human_readable_summary(
            health_state
        )
    )
    assert exit_code == karabiner_status_cli_module.EXIT_CODE_HEALTHY


def test_summary_exits_nonzero_for_process_not_running(karabiner_status_cli_module):
    health_state = {
        "karabiner_core_service_process_running": False,
        "karabiner_console_user_server_process_running": True,
        "karabiner_cli_ipc_probe_succeeded": True,
        "last_health_probe_epoch": time.time(),
        "daemon_process_id": 123,
        "daemon_started_epoch": time.time() - 60,
    }
    _summary, exit_code = (
        karabiner_status_cli_module.format_health_state_as_human_readable_summary(
            health_state
        )
    )
    assert exit_code == karabiner_status_cli_module.EXIT_CODE_DEGRADED


def test_summary_exits_nonzero_for_ipc_probe_failure(karabiner_status_cli_module):
    health_state = {
        "karabiner_core_service_process_running": True,
        "karabiner_console_user_server_process_running": True,
        "karabiner_cli_ipc_probe_succeeded": False,
        "karabiner_cli_ipc_probe_failure_reason": "timed out",
        "last_health_probe_epoch": time.time(),
        "daemon_process_id": 123,
        "daemon_started_epoch": time.time() - 60,
    }
    _summary, exit_code = (
        karabiner_status_cli_module.format_health_state_as_human_readable_summary(
            health_state
        )
    )
    assert exit_code == karabiner_status_cli_module.EXIT_CODE_DEGRADED


def test_summary_exits_nonzero_for_missing_health_file(karabiner_status_cli_module):
    _summary, exit_code = (
        karabiner_status_cli_module.format_health_state_as_human_readable_summary(None)
    )
    assert exit_code == karabiner_status_cli_module.EXIT_CODE_DEGRADED
