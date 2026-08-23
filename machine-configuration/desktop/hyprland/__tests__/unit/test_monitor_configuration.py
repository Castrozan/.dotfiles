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
