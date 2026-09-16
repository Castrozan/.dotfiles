from unittest.mock import MagicMock, patch
from network_management import network_manager


class TestGetActiveConnection:
    def test_returns_first_non_loopback_connection(self):
        mock_result = MagicMock()
        mock_result.stdout = "MyWiFi:802-11-wireless:wlan0\nlo:loopback:lo\n"

        with patch(
            "network_management.network_manager.subprocess.run",
            return_value=mock_result,
        ):
            assert (
                network_manager.get_active_connection()
                == "MyWiFi:802-11-wireless:wlan0"
            )

    def test_returns_empty_when_only_loopback(self):
        mock_result = MagicMock()
        mock_result.stdout = "lo:loopback:lo\n"

        with patch(
            "network_management.network_manager.subprocess.run",
            return_value=mock_result,
        ):
            assert network_manager.get_active_connection() == ""

    def test_returns_empty_when_no_connections(self):
        mock_result = MagicMock()
        mock_result.stdout = ""

        with patch(
            "network_management.network_manager.subprocess.run",
            return_value=mock_result,
        ):
            assert network_manager.get_active_connection() == ""


class TestHasSavedConnection:
    def test_returns_true_when_connection_saved(self):
        mock_result = MagicMock()
        mock_result.stdout = "MyWiFi\nOtherNet\n"

        with patch(
            "network_management.network_manager.subprocess.run",
            return_value=mock_result,
        ):
            assert network_manager.has_saved_connection("MyWiFi") is True

    def test_returns_false_when_not_saved(self):
        mock_result = MagicMock()
        mock_result.stdout = "OtherNet\n"

        with patch(
            "network_management.network_manager.subprocess.run",
            return_value=mock_result,
        ):
            assert network_manager.has_saved_connection("MyWiFi") is False


class TestGetActiveConnectionNames:
    def test_returns_active_names(self):
        mock_result = MagicMock()
        mock_result.stdout = "MyWiFi\nVPN\n"

        with patch(
            "network_management.network_manager.subprocess.run",
            return_value=mock_result,
        ):
            names = network_manager.get_active_connection_names()
            assert names == {"MyWiFi", "VPN"}


class TestGetSavedConnections:
    def test_parses_connections(self):
        mock_result = MagicMock()
        mock_result.stdout = "HomeNet:802-11-wireless\nWork:802-3-ethernet\n"

        with patch(
            "network_management.network_manager.subprocess.run",
            return_value=mock_result,
        ):
            connections = network_manager.get_saved_connections()
            assert len(connections) == 2
            assert connections[0]["name"] == "HomeNet"
            assert connections[0]["type"] == "802-11-wireless"

    def test_skips_loopback(self):
        mock_result = MagicMock()
        mock_result.stdout = "lo:loopback\nHomeNet:802-11-wireless\n"

        with patch(
            "network_management.network_manager.subprocess.run",
            return_value=mock_result,
        ):
            connections = network_manager.get_saved_connections()
            assert len(connections) == 1
            assert connections[0]["name"] == "HomeNet"
