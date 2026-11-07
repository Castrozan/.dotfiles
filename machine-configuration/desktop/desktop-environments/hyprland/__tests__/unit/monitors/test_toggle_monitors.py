import threading
from unittest.mock import patch

import monitor_configuration
import pytest
import toggle_monitors
from monitor_configuration import ConnectedMonitors, DisplayMode

LAPTOP_WITH_ACER = ConnectedMonitors(internal="eDP-1", externals=("DP-1",))


@pytest.fixture
def acer_connected_with_lid_open(monitor_state_files, monkeypatch):
    monkeypatch.setattr(
        toggle_monitors, "read_connected_monitors", lambda: LAPTOP_WITH_ACER
    )
    monkeypatch.setattr(toggle_monitors, "laptop_lid_is_closed", lambda: False)
    with (
        patch("monitor_configuration.run_hyprctl"),
        patch("monitor_configuration.migrate_workspaces_from_disabled_monitors"),
    ):
        yield


class TestDetermineNextMode:
    @pytest.mark.parametrize(
        ("current_mode", "next_mode"),
        [
            (DisplayMode.EXTERNAL, DisplayMode.EXTENDED),
            (DisplayMode.EXTENDED, DisplayMode.INTERNAL),
            (DisplayMode.INTERNAL, DisplayMode.EXTERNAL),
        ],
    )
    def test_cycles_all_modes_with_the_lid_open(self, current_mode, next_mode):
        assert toggle_monitors.determine_next_mode(current_mode, False) is next_mode

    @pytest.mark.parametrize(
        ("current_mode", "next_mode"),
        [
            (DisplayMode.EXTENDED, DisplayMode.EXTERNAL),
            (DisplayMode.EXTERNAL, DisplayMode.EXTENDED),
            (DisplayMode.INTERNAL, DisplayMode.EXTENDED),
        ],
    )
    def test_skips_built_in_only_with_the_lid_closed(self, current_mode, next_mode):
        assert toggle_monitors.determine_next_mode(current_mode, True) is next_mode


class TestToggleDisplayMode:
    def test_advances_from_the_stored_mode_not_the_live_outputs(
        self, acer_connected_with_lid_open
    ):
        monitor_configuration.write_display_mode(DisplayMode.EXTERNAL)
        assert toggle_monitors.toggle_display_mode() == "Extended"
        assert toggle_monitors.toggle_display_mode() == "Built-in only"
        assert toggle_monitors.toggle_display_mode() == "External only"
        assert monitor_configuration.read_display_mode() is DisplayMode.EXTERNAL

    def test_concurrent_presses_each_advance_the_mode(
        self, acer_connected_with_lid_open
    ):
        monitor_configuration.write_display_mode(DisplayMode.EXTERNAL)
        presses = [
            threading.Thread(target=toggle_monitors.toggle_display_mode)
            for _ in range(2)
        ]
        for press in presses:
            press.start()
        for press in presses:
            press.join()
        assert monitor_configuration.read_display_mode() is DisplayMode.INTERNAL

    def test_keeps_the_stored_mode_while_no_external_is_connected(
        self, monitor_state_files, monkeypatch
    ):
        monitor_configuration.write_display_mode(DisplayMode.EXTENDED)
        monitor_configuration.OVERRIDE_FILE.write_text(
            "monitor = eDP-1, preferred, auto, 1"
        )
        monkeypatch.setattr(
            toggle_monitors,
            "read_connected_monitors",
            lambda: ConnectedMonitors(internal="eDP-1", externals=()),
        )
        assert toggle_monitors.toggle_display_mode() == "No external monitor connected"
        assert monitor_configuration.read_display_mode() is DisplayMode.EXTENDED

    def test_reports_a_missing_internal_panel(self, monitor_state_files, monkeypatch):
        monkeypatch.setattr(
            toggle_monitors,
            "read_connected_monitors",
            lambda: ConnectedMonitors(internal=None, externals=("DP-1",)),
        )
        assert toggle_monitors.toggle_display_mode() == "No internal monitor found"
