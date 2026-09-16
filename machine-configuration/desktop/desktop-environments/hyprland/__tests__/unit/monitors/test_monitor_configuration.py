import time
from pathlib import Path
from unittest.mock import call, patch

import monitor_configuration


class TestFindEnabledConfigLineForMonitor:
    def test_falls_back_to_preferred_when_the_config_is_missing(self, tmp_path):
        with patch.object(
            monitor_configuration, "MONITORS_CONF", tmp_path / "nonexistent.conf"
        ):
            assert (
                monitor_configuration.find_enabled_config_line_for_monitor("eDP-1")
                == "eDP-1, preferred, auto, 1"
            )

    def test_returns_the_configured_line_without_its_keyword(self, tmp_path):
        config_file = tmp_path / "monitors.conf"
        config_file.write_text(
            "monitor = HDMI-A-1, 1920x1080, 0x0, 1\n"
            "  monitor = eDP-1, 2880x1800@120, 0x1080, 1.5\n"
        )

        with patch.object(monitor_configuration, "MONITORS_CONF", config_file):
            assert (
                monitor_configuration.find_enabled_config_line_for_monitor("eDP-1")
                == "eDP-1, 2880x1800@120, 0x1080, 1.5"
            )

    def test_falls_back_to_preferred_when_the_configured_line_disables_it(
        self, tmp_path
    ):
        config_file = tmp_path / "monitors.conf"
        config_file.write_text("monitor = eDP-1, disable\n")

        with patch.object(monitor_configuration, "MONITORS_CONF", config_file):
            assert (
                monitor_configuration.find_enabled_config_line_for_monitor("eDP-1")
                == "eDP-1, preferred, auto, 1"
            )

    def test_ignores_lines_belonging_to_another_monitor(self, tmp_path):
        config_file = tmp_path / "monitors.conf"
        config_file.write_text("monitor = eDP-11, 1920x1080, 0x0, 1\n")

        with patch.object(monitor_configuration, "MONITORS_CONF", config_file):
            assert (
                monitor_configuration.find_enabled_config_line_for_monitor("eDP-1")
                == "eDP-1, preferred, auto, 1"
            )


class TestMonitorOverridePaths:
    def test_the_override_and_toggle_lock_live_in_the_user_cache(self):
        assert (
            monitor_configuration.OVERRIDE_FILE
            == Path.home() / ".cache" / "hypr-monitors-override.conf"
        )
        assert (
            monitor_configuration.TOGGLE_LOCK_FILE
            == Path.home() / ".cache" / "hypr-monitors-toggle.lock"
        )


class TestWriteToggleLock:
    def test_stamps_the_lock_file_with_the_current_time(self, tmp_path):
        lock_file = tmp_path / "toggle.lock"

        with patch.object(monitor_configuration, "TOGGLE_LOCK_FILE", lock_file):
            monitor_configuration.write_toggle_lock()

        assert abs(float(lock_file.read_text()) - time.time()) < 5


class TestWriteOverrideAndReload:
    def test_takes_the_toggle_lock_then_writes_the_override_and_reloads(self, tmp_path):
        override_file = tmp_path / "override.conf"
        lock_file = tmp_path / "toggle.lock"

        with patch.object(monitor_configuration, "OVERRIDE_FILE", override_file):
            with patch.object(monitor_configuration, "TOGGLE_LOCK_FILE", lock_file):
                with patch("monitor_configuration.run_hyprctl") as mock_run_hyprctl:
                    monitor_configuration.write_override_and_reload(
                        "monitor = eDP-1, disable"
                    )

        assert override_file.read_text() == "monitor = eDP-1, disable"
        assert lock_file.exists()
        assert mock_run_hyprctl.call_args_list == [call("reload")]


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
