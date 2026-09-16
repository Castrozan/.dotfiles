from unittest.mock import patch
from network_management import network_manager


class TestToggleWifi:
    def test_disables_when_enabled(self):
        with patch(
            "network_management.network_manager.get_wifi_status", return_value="enabled"
        ):
            with patch("network_management.network_manager.subprocess.run") as mock_run:
                with patch("network_management.network_prompts.notify"):
                    network_manager.toggle_wifi()

                    mock_run.assert_called_once_with(
                        ["nmcli", "radio", "wifi", "off"],
                        capture_output=True,
                    )

    def test_enables_when_disabled(self):
        with patch(
            "network_management.network_manager.get_wifi_status",
            return_value="disabled",
        ):
            with patch("network_management.network_manager.subprocess.run") as mock_run:
                with patch("network_management.network_prompts.notify"):
                    network_manager.toggle_wifi()

                    mock_run.assert_called_once_with(
                        ["nmcli", "radio", "wifi", "on"],
                        capture_output=True,
                    )
