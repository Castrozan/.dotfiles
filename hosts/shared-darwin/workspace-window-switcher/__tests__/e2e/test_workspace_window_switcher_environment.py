#!/usr/bin/env python3

import pytest

from workspace_window_switcher_helpers import (
    is_karabiner_core_service_running,
)

pytestmark = pytest.mark.workspace_switcher_integration


def test_karabiner_core_service_is_running():
    assert is_karabiner_core_service_running(), (
        "Karabiner-Core-Service process not found; Cmd+Tab workspace switching depends"
        " on Karabiner intercepting the keystroke at the HID layer. Open"
        " Karabiner-Elements.app or run: launchctl kickstart -k"
        " system/org.pqrs.service.daemon.Karabiner-DriverKit-VirtualHIDDeviceClient"
    )
