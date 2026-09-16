from unittest.mock import MagicMock, patch
from network_management import network_manager


class TestGetWifiStatus:
    def test_returns_enabled(self):
        mock_result = MagicMock()
        mock_result.stdout = "enabled\n"

        with patch(
            "network_management.network_manager.subprocess.run",
            return_value=mock_result,
        ):
            assert network_manager.get_wifi_status() == "enabled"

    def test_returns_disabled(self):
        mock_result = MagicMock()
        mock_result.stdout = "disabled\n"

        with patch(
            "network_management.network_manager.subprocess.run",
            return_value=mock_result,
        ):
            assert network_manager.get_wifi_status() == "disabled"


class TestGetWifiNetworks:
    def test_parses_network_list(self):
        mock_result = MagicMock()
        mock_result.stdout = "HomeNet:85:WPA2:*\nCafeWifi:60:WPA2:\nOpenNet:30::\n"

        with patch(
            "network_management.network_manager.subprocess.run",
            return_value=mock_result,
        ):
            networks = network_manager.get_wifi_networks()

            assert len(networks) == 3
            assert networks[0]["ssid"] == "HomeNet"
            assert networks[0]["signal"] == "85"
            assert networks[0]["in_use"] == "*"

    def test_deduplicates_by_ssid(self):
        mock_result = MagicMock()
        mock_result.stdout = "Net1:80:WPA2:\nNet1:60:WPA2:\nNet2:50:WPA2:\n"

        with patch(
            "network_management.network_manager.subprocess.run",
            return_value=mock_result,
        ):
            networks = network_manager.get_wifi_networks()

            assert len(networks) == 2

    def test_skips_empty_ssids(self):
        mock_result = MagicMock()
        mock_result.stdout = ":80:WPA2:\nNet1:60:WPA2:\n"

        with patch(
            "network_management.network_manager.subprocess.run",
            return_value=mock_result,
        ):
            networks = network_manager.get_wifi_networks()

            assert len(networks) == 1
            assert networks[0]["ssid"] == "Net1"

    def test_sorts_by_signal_descending(self):
        mock_result = MagicMock()
        mock_result.stdout = "Weak:20:WPA2:\nStrong:90:WPA2:\nMedium:50:WPA2:\n"

        with patch(
            "network_management.network_manager.subprocess.run",
            return_value=mock_result,
        ):
            networks = network_manager.get_wifi_networks()

            assert networks[0]["ssid"] == "Strong"
            assert networks[1]["ssid"] == "Medium"
            assert networks[2]["ssid"] == "Weak"


class TestIsEnterpriseNetwork:
    def test_returns_true_for_enterprise(self):
        mock_result = MagicMock()
        mock_result.stdout = "CorpNet:WPA2 802.1X\nHomeNet:WPA2\n"

        with patch(
            "network_management.network_manager.subprocess.run",
            return_value=mock_result,
        ):
            assert network_manager.is_enterprise_network("CorpNet") is True

    def test_returns_false_for_non_enterprise(self):
        mock_result = MagicMock()
        mock_result.stdout = "HomeNet:WPA2\n"

        with patch(
            "network_management.network_manager.subprocess.run",
            return_value=mock_result,
        ):
            assert network_manager.is_enterprise_network("HomeNet") is False
