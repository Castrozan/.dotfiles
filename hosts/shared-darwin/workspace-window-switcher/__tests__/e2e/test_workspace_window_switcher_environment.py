#!/usr/bin/env python3

import pytest

from workspace_window_switcher_helpers import (
    is_karabiner_core_service_running,
)

pytestmark = pytest.mark.workspace_switcher_integration


def test_karabiner_core_service_is_running():
    print(
        "TEST: Karabiner-Core-Service is running"
        " (hosts the HID grabber that intercepts Cmd+Tab)"
    )

    if not is_karabiner_core_service_running():
        print("  FAIL: Karabiner-Core-Service process not found")
        print("        Cmd+Tab workspace switching depends on Karabiner intercepting")
        print("        the keystroke at the HID layer. Open Karabiner-Elements.app")
        print(
            "        or run: launchctl kickstart -k system/org.pqrs.service.daemon.Karabiner-DriverKit-VirtualHIDDeviceClient"
        )
        return False

    print("  PASS")
    return True
