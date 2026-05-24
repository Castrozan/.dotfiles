import importlib.machinery
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PYOBJC_FRAMEWORK_MODULES_TO_MOCK = [
    "AppKit",
    "Foundation",
    "PyObjCTools",
    "PyObjCTools.AppHelper",
]

for pyobjc_framework_module_name in PYOBJC_FRAMEWORK_MODULES_TO_MOCK:
    sys.modules.setdefault(pyobjc_framework_module_name, MagicMock())

KARABINER_RESTART_ON_WAKE_DAEMON_SCRIPT_PATH = (
    Path(__file__).parent.parent
    / "restart-on-wake"
    / "scripts"
    / "karabiner-restart-on-wake-daemon"
)

KARABINER_STATUS_CLI_SCRIPT_PATH = (
    Path(__file__).parent.parent / "status" / "scripts" / "karabiner-status"
)


def _load_module_from_path(module_name, module_file_path):
    loader = importlib.machinery.SourceFileLoader(module_name, str(module_file_path))
    spec = importlib.util.spec_from_loader(module_name, loader)
    loaded_module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = loaded_module
    spec.loader.exec_module(loaded_module)
    return loaded_module


@pytest.fixture
def karabiner_restart_on_wake_daemon_module():
    return _load_module_from_path(
        "karabiner_restart_on_wake_daemon",
        KARABINER_RESTART_ON_WAKE_DAEMON_SCRIPT_PATH,
    )


@pytest.fixture
def karabiner_status_cli_module():
    return _load_module_from_path(
        "karabiner_status_cli", KARABINER_STATUS_CLI_SCRIPT_PATH
    )


@pytest.fixture
def temporary_daemon_state_paths(tmp_path):
    health_state_file_path = tmp_path / "karabiner-health.json"
    structured_event_log_file_path = tmp_path / "karabiner-daemon.log"
    return {
        "health_state_file_path": str(health_state_file_path),
        "structured_event_log_file_path": str(structured_event_log_file_path),
    }


@pytest.fixture
def daemon_module_with_temporary_paths(
    karabiner_restart_on_wake_daemon_module, temporary_daemon_state_paths, monkeypatch
):
    monkeypatch.setattr(
        karabiner_restart_on_wake_daemon_module,
        "DAEMON_HEALTH_STATE_FILE_PATH",
        temporary_daemon_state_paths["health_state_file_path"],
    )
    monkeypatch.setattr(
        karabiner_restart_on_wake_daemon_module,
        "DAEMON_STRUCTURED_EVENT_LOG_FILE_PATH",
        temporary_daemon_state_paths["structured_event_log_file_path"],
    )
    return karabiner_restart_on_wake_daemon_module


@pytest.fixture
def status_cli_module_with_temporary_paths(
    karabiner_status_cli_module, temporary_daemon_state_paths, monkeypatch
):
    monkeypatch.setattr(
        karabiner_status_cli_module,
        "DAEMON_HEALTH_STATE_FILE_PATH",
        temporary_daemon_state_paths["health_state_file_path"],
    )
    monkeypatch.setattr(
        karabiner_status_cli_module,
        "DAEMON_STRUCTURED_EVENT_LOG_FILE_PATH",
        temporary_daemon_state_paths["structured_event_log_file_path"],
    )
    return karabiner_status_cli_module


def _build_completed_process_with_exit_zero(stdout_text=""):
    completion = MagicMock()
    completion.returncode = 0
    completion.stdout = stdout_text
    return completion


def _build_completed_process_with_exit_one(stdout_text=""):
    completion = MagicMock()
    completion.returncode = 1
    completion.stdout = stdout_text
    return completion


def _build_karabiner_cli_list_connected_devices_json_with_one_keyboard():
    return json.dumps(
        [{"device_identifiers": {"is_keyboard": True, "product_id": 1, "vendor_id": 1}}]
    )


def _build_fake_subprocess_run_router(call_route_map):
    def fake_subprocess_run(command_line_arguments, **_kwargs):
        first_argument = command_line_arguments[0]
        second_argument = (
            command_line_arguments[1] if len(command_line_arguments) > 1 else ""
        )
        if first_argument == "/usr/bin/pgrep":
            return call_route_map["pgrep"]
        if "karabiner_cli" in first_argument:
            if second_argument == "--show-current-profile-name":
                return call_route_map["karabiner_cli_profile"]
            if second_argument == "--list-connected-devices":
                return call_route_map["karabiner_cli_devices"]
        if "launchctl" in first_argument:
            return call_route_map.get(
                "launchctl", _build_completed_process_with_exit_zero()
            )
        return _build_completed_process_with_exit_zero()

    return fake_subprocess_run


@pytest.fixture
def make_completed_process_with_exit_zero():
    return _build_completed_process_with_exit_zero


@pytest.fixture
def make_completed_process_with_exit_one():
    return _build_completed_process_with_exit_one


@pytest.fixture
def karabiner_cli_list_connected_devices_json_with_one_keyboard():
    return _build_karabiner_cli_list_connected_devices_json_with_one_keyboard()


@pytest.fixture
def route_subprocess_run_to_fake_completions():
    return _build_fake_subprocess_run_router
