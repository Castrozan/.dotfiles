from unittest.mock import MagicMock, patch

import pytest
from network_management import network_manager


class TestGetActiveConnection:
    @pytest.mark.parametrize(
        ("stdout", "expected_connection"),
        [
            pytest.param(
                "MyWiFi:802-11-wireless:wlan0\nlo:loopback:lo\n",
                "MyWiFi:802-11-wireless:wlan0",
                id="returns_first_non_loopback_connection",
            ),
            pytest.param(
                "lo:loopback:lo\n",
                "",
                id="returns_empty_when_only_loopback",
            ),
            pytest.param("", "", id="returns_empty_when_no_connections"),
        ],
    )
    def test_selects_the_first_non_loopback_connection(
        self, stdout, expected_connection
    ):
        mock_result = MagicMock()
        mock_result.stdout = stdout

        with patch(
            "network_management.network_manager.subprocess.run",
            return_value=mock_result,
        ):
            assert network_manager.get_active_connection() == expected_connection


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
