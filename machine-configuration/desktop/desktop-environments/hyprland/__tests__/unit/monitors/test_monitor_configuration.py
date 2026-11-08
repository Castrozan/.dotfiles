from pathlib import Path
from unittest.mock import call, patch

import monitor_configuration
import pytest
from monitor_configuration import ConnectedMonitors, DisplayMode


LAPTOP_WITH_ACER = ConnectedMonitors(internal="eDP-1", externals=("DP-1",))
LAPTOP_ALONE = ConnectedMonitors(internal="eDP-1", externals=())


class TestFindEnabledConfigLineForMonitor:
    def test_falls_back_to_preferred_when_the_config_is_missing(self, tmp_path):
        with patch.object(
            monitor_configuration, "MONITORS_CONF", tmp_path / "nonexistent.conf"
        ):
            assert (
                monitor_configuration.find_enabled_config_line_for_monitor("eDP-1")
                == "eDP-1, preferred, auto, 1"
            )

    @pytest.mark.parametrize(
        ("config_text", "expected_line"),
        [
            pytest.param(
                "monitor = HDMI-A-1, 1920x1080, 0x0, 1\n"
                "  monitor = eDP-1, 2880x1800@120, 0x1080, 1.5\n",
                "eDP-1, 2880x1800@120, 0x1080, 1.5",
                id="returns_the_configured_line_without_its_keyword",
            ),
            pytest.param(
                "monitor = eDP-1, disable\n",
                "eDP-1, preferred, auto, 1",
                id="falls_back_to_preferred_when_the_configured_line_disables_it",
            ),
            pytest.param(
                "monitor = eDP-11, 1920x1080, 0x0, 1\n",
                "eDP-1, preferred, auto, 1",
                id="ignores_lines_belonging_to_another_monitor",
            ),
        ],
    )
    def test_resolves_the_enabled_config_line_for_the_monitor(
        self, tmp_path, config_text, expected_line
    ):
        config_file = tmp_path / "monitors.conf"
        config_file.write_text(config_text)

        with patch.object(monitor_configuration, "MONITORS_CONF", config_file):
            assert (
                monitor_configuration.find_enabled_config_line_for_monitor("eDP-1")
                == expected_line
            )


class TestMonitorStatePaths:
    def test_the_override_mode_and_lock_live_in_the_user_cache(self):
        cache = Path.home() / ".cache"
        assert (
            monitor_configuration.OVERRIDE_FILE == cache / "hypr-monitors-override.conf"
        )
        assert monitor_configuration.DISPLAY_MODE_FILE == cache / "hypr-monitors-mode"
        assert monitor_configuration.RECONCILE_LOCK_FILE == cache / "hypr-monitors.lock"


class TestClassifyMonitorNames:
    def test_separates_internal_from_externals_regardless_of_order(
        self, monitor_state_files
    ):
        assert monitor_configuration.classify_monitor_names(
            ["DP-1", "eDP-1", "HDMI-A-1"]
        ) == ConnectedMonitors(internal="eDP-1", externals=("DP-1", "HDMI-A-1"))

    def test_ignores_placeholder_outputs_seen_during_hotplug(self, monitor_state_files):
        assert (
            monitor_configuration.classify_monitor_names(["FALLBACK", "", "eDP-1"])
            == LAPTOP_ALONE
        )

    def test_takes_the_internal_name_from_config_when_hyprland_omits_it(
        self, tmp_path, monkeypatch
    ):
        config_file = tmp_path / "monitors.conf"
        config_file.write_text("monitor = eDP-2, disable\n")
        monkeypatch.setattr(monitor_configuration, "MONITORS_CONF", config_file)
        assert monitor_configuration.classify_monitor_names(
            ["DP-1"]
        ) == ConnectedMonitors(internal="eDP-2", externals=("DP-1",))


class TestRenderOverride:
    def test_external_mode_keeps_the_base_config(self, monitor_state_files):
        assert (
            monitor_configuration.render_override(
                DisplayMode.EXTERNAL, LAPTOP_WITH_ACER
            )
            == ""
        )

    def test_extended_mode_enables_the_internal_panel(self, monitor_state_files):
        assert (
            monitor_configuration.render_override(
                DisplayMode.EXTENDED, LAPTOP_WITH_ACER
            )
            == "monitor = eDP-1, preferred, auto, 1"
        )

    def test_internal_mode_disables_every_external(self, monitor_state_files):
        assert monitor_configuration.render_override(
            DisplayMode.INTERNAL,
            ConnectedMonitors(internal="eDP-1", externals=("DP-1", "HDMI-A-1")),
        ) == (
            "monitor = eDP-1, preferred, auto, 1\n"
            "monitor = DP-1, disable\n"
            "monitor = HDMI-A-1, disable\n"
            "monitor = , disable"
        )

    @pytest.mark.parametrize("mode", list(DisplayMode))
    def test_any_mode_enables_the_internal_panel_without_an_external(
        self, monitor_state_files, mode
    ):
        assert (
            monitor_configuration.render_override(mode, LAPTOP_ALONE)
            == "monitor = eDP-1, preferred, auto, 1"
        )


class TestDisplayModePersistence:
    def test_defaults_to_external_when_nothing_was_chosen(self, monitor_state_files):
        assert monitor_configuration.read_display_mode() is DisplayMode.EXTERNAL

    def test_defaults_to_external_when_the_stored_mode_is_unknown(
        self, monitor_state_files
    ):
        monitor_configuration.DISPLAY_MODE_FILE.write_text("mirrored")
        assert monitor_configuration.read_display_mode() is DisplayMode.EXTERNAL

    def test_round_trips_the_chosen_mode(self, monitor_state_files):
        monitor_configuration.write_display_mode(DisplayMode.EXTENDED)
        assert monitor_configuration.read_display_mode() is DisplayMode.EXTENDED


class TestSendMonitorNotification:
    def test_sends_a_transient_monitor_notification(self):
        with patch("monitor_configuration.subprocess.run") as mock_run:
            monitor_configuration.send_monitor_notification("Built-in only")

            assert mock_run.call_args_list == [
                call(
                    ["notify-send", "-t", "2000", "Monitor", "Built-in only"],
                    capture_output=True,
                )
            ]
