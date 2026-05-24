import json


def test_read_health_state_returns_none_when_file_missing(
    status_cli_module_with_temporary_paths,
):
    assert (
        status_cli_module_with_temporary_paths.read_health_state_from_file_or_none()
        is None
    )


def test_read_health_state_returns_parsed_json_when_file_present(
    status_cli_module_with_temporary_paths,
):
    test_payload = {
        "kick_count_total": 7,
        "karabiner_core_service_process_running": True,
        "karabiner_console_user_server_process_running": True,
    }
    with open(
        status_cli_module_with_temporary_paths.DAEMON_HEALTH_STATE_FILE_PATH, "w"
    ) as health_state_file:
        json.dump(test_payload, health_state_file)
    assert (
        status_cli_module_with_temporary_paths.read_health_state_from_file_or_none()
        == test_payload
    )


def test_read_health_state_returns_none_when_file_is_corrupt_json(
    status_cli_module_with_temporary_paths,
):
    with open(
        status_cli_module_with_temporary_paths.DAEMON_HEALTH_STATE_FILE_PATH, "w"
    ) as health_state_file:
        health_state_file.write("not valid json {{{")
    assert (
        status_cli_module_with_temporary_paths.read_health_state_from_file_or_none()
        is None
    )
