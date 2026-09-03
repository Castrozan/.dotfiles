import plistlib
from pathlib import Path

import pytest

from set_wifi_ipv6_link_local import (
    LINK_LOCAL_CONFIG_METHOD,
    NETWORKSETUP_BINARY_PATH,
    WIFI_NETWORK_SERVICE_NAME,
    reconcile_wifi_ipv6_link_local,
)

EXPECTED_LINK_LOCAL_COMMAND = [
    NETWORKSETUP_BINARY_PATH,
    "-setv6LinkLocal",
    WIFI_NETWORK_SERVICE_NAME,
]


def network_service(name: str, ipv6_config_method: str) -> dict:
    return {"UserDefinedName": name, "IPv6": {"ConfigMethod": ipv6_config_method}}


def write_preferences(directory: Path, services: dict) -> Path:
    preferences_path = directory / "preferences.plist"
    preferences_path.write_bytes(plistlib.dumps({"NetworkServices": services}))
    return preferences_path


@pytest.fixture
def recorded_commands() -> list[list[str]]:
    return []


@pytest.fixture
def recording_runner(recorded_commands):
    def record(command):
        recorded_commands.append(list(command))

    return record


def test_pins_wifi_to_link_local_when_ipv6_is_automatic(
    tmp_path, recording_runner, recorded_commands
):
    preferences_path = write_preferences(
        tmp_path,
        {
            "wifi": network_service(WIFI_NETWORK_SERVICE_NAME, "Automatic"),
            "bridge": network_service("Thunderbolt Bridge", "Automatic"),
        },
    )

    changed = reconcile_wifi_ipv6_link_local(preferences_path, recording_runner)

    assert changed is True
    assert recorded_commands == [EXPECTED_LINK_LOCAL_COMMAND]


def test_leaves_other_services_alone(tmp_path, recording_runner, recorded_commands):
    preferences_path = write_preferences(
        tmp_path,
        {
            "wifi": network_service(
                WIFI_NETWORK_SERVICE_NAME, LINK_LOCAL_CONFIG_METHOD
            ),
            "bridge": network_service("Thunderbolt Bridge", "Automatic"),
        },
    )

    changed = reconcile_wifi_ipv6_link_local(preferences_path, recording_runner)

    assert changed is False
    assert recorded_commands == []


def test_skips_when_no_wifi_service_exists(
    tmp_path, recording_runner, recorded_commands
):
    preferences_path = write_preferences(
        tmp_path, {"bridge": network_service("Thunderbolt Bridge", "Automatic")}
    )

    changed = reconcile_wifi_ipv6_link_local(preferences_path, recording_runner)

    assert changed is False
    assert recorded_commands == []


def test_skips_when_preferences_file_is_missing(
    tmp_path, recording_runner, recorded_commands
):
    changed = reconcile_wifi_ipv6_link_local(
        tmp_path / "missing.plist", recording_runner
    )

    assert changed is False
    assert recorded_commands == []
