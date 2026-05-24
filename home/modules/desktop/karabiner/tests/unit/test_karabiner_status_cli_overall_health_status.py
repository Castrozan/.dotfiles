import time


def test_health_status_is_healthy_when_both_processes_running_and_ipc_probe_succeeded(
    karabiner_status_cli_module,
):
    health_state = {
        "karabiner_core_service_process_running": True,
        "karabiner_console_user_server_process_running": True,
        "karabiner_cli_ipc_probe_succeeded": True,
        "last_health_probe_epoch": time.time(),
    }
    assert (
        karabiner_status_cli_module.determine_overall_health_status_from_state(
            health_state
        )
        == "HEALTHY"
    )


def test_health_status_is_degraded_when_ipc_probe_failed(karabiner_status_cli_module):
    health_state = {
        "karabiner_core_service_process_running": True,
        "karabiner_console_user_server_process_running": True,
        "karabiner_cli_ipc_probe_succeeded": False,
        "karabiner_cli_ipc_probe_failure_reason": "show-current-profile-name timed out",
        "last_health_probe_epoch": time.time(),
    }
    assert "DEGRADED" in (
        karabiner_status_cli_module.determine_overall_health_status_from_state(
            health_state
        )
    )


def test_health_status_is_degraded_when_core_service_not_running(
    karabiner_status_cli_module,
):
    health_state = {
        "karabiner_core_service_process_running": False,
        "karabiner_console_user_server_process_running": True,
    }
    assert (
        "DEGRADED"
        in karabiner_status_cli_module.determine_overall_health_status_from_state(
            health_state
        )
    )


def test_health_status_is_degraded_when_console_user_server_not_running(
    karabiner_status_cli_module,
):
    health_state = {
        "karabiner_core_service_process_running": True,
        "karabiner_console_user_server_process_running": False,
    }
    assert (
        "DEGRADED"
        in karabiner_status_cli_module.determine_overall_health_status_from_state(
            health_state
        )
    )


def test_health_status_is_no_file_when_state_is_none(karabiner_status_cli_module):
    assert (
        karabiner_status_cli_module.determine_overall_health_status_from_state(None)
        == "NO HEALTH FILE"
    )


def test_health_status_is_unknown_when_no_health_probe_yet(
    karabiner_status_cli_module,
):
    health_state = {
        "daemon_started_epoch": time.time(),
        "karabiner_core_service_process_running": True,
        "karabiner_console_user_server_process_running": True,
    }
    assert (
        "UNKNOWN"
        in karabiner_status_cli_module.determine_overall_health_status_from_state(
            health_state
        )
    )
