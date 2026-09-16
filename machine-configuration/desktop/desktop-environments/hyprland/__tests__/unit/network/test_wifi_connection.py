from unittest.mock import patch
from network_management import wifi_connection


class TestConnectWifi:
    def test_uses_saved_connection_when_available(self):
        with patch(
            "network_management.network_manager.has_saved_connection", return_value=True
        ):
            with patch(
                "network_management.wifi_connection.connect_to_saved_connection"
            ) as mock_connect:
                wifi_connection.connect_wifi("MyWiFi")
                mock_connect.assert_called_once_with("MyWiFi")

    def test_uses_enterprise_when_detected(self):
        with patch(
            "network_management.network_manager.has_saved_connection",
            return_value=False,
        ):
            with patch(
                "network_management.network_manager.is_enterprise_network",
                return_value=True,
            ):
                with patch(
                    "network_management.wifi_connection.connect_to_enterprise_wifi"
                ) as mock_connect:
                    wifi_connection.connect_wifi("CorpNet")
                    mock_connect.assert_called_once_with("CorpNet")

    def test_uses_password_for_regular_network(self):
        with patch(
            "network_management.network_manager.has_saved_connection",
            return_value=False,
        ):
            with patch(
                "network_management.network_manager.is_enterprise_network",
                return_value=False,
            ):
                with patch(
                    "network_management.wifi_connection.connect_to_wifi_with_password"
                ) as mock_connect:
                    wifi_connection.connect_wifi("CafeWifi")
                    mock_connect.assert_called_once_with("CafeWifi")
