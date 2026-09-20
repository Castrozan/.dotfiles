import importlib.util
import os
import socket
import sys
from pathlib import Path

SCRIPTS_DIRECTORY = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIRECTORY))
LIFECYCLE_PATH = SCRIPTS_DIRECTORY / "on_demand_proxy_lifecycle.py"
LIFECYCLE_SPECIFICATION = importlib.util.spec_from_file_location(
    "on_demand_proxy_lifecycle", LIFECYCLE_PATH
)
assert LIFECYCLE_SPECIFICATION
assert LIFECYCLE_SPECIFICATION.loader
LIFECYCLE = importlib.util.module_from_spec(LIFECYCLE_SPECIFICATION)
LIFECYCLE_SPECIFICATION.loader.exec_module(LIFECYCLE)

import pytest
import service_commands as COMMANDS

def test_the_launchd_commands_name_the_current_user_domain():
    label = "com.dotfiles.cli-proxy-api"
    assert COMMANDS.start_command_for("launchd", label) == [
        "launchctl",
        "kickstart",
        f"gui/{os.getuid()}/{label}",
    ]
    assert COMMANDS.stop_command_for("launchd", label) == [
        "launchctl",
        "kill",
        "SIGTERM",
        f"gui/{os.getuid()}/{label}",
    ], (
        "bootout would unload the agent and the next session could not kickstart it"
    )


def test_the_systemd_commands_address_the_user_unit():
    unit = "cli-proxy-api.service"
    assert COMMANDS.start_command_for("systemd", unit) == [
        "systemctl",
        "--user",
        "start",
        unit,
    ]
    assert COMMANDS.stop_command_for("systemd", unit) == [
        "systemctl",
        "--user",
        "stop",
        unit,
    ]


def test_a_label_outside_the_allowed_shape_is_refused():
    for rejected in ["", "has space", "semi;colon", "slash/label", "-leading-dash"]:
        with pytest.raises(ValueError):
            COMMANDS.start_command_for("launchd", rejected)


def test_a_missing_service_controller_binary_does_not_crash_the_launcher():
    COMMANDS.run_service_command(["a-binary-no-host-has", "kickstart"])
