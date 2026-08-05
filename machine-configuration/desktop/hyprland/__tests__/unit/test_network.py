from unittest.mock import MagicMock, patch

import network


class TestGetActiveConnection:
    def test_returns_first_non_loopback_connection(self):
        mock_result = MagicMock()
        mock_result.stdout = "MyWiFi:802-11-wireless:wlan0\nlo:loopback:lo\n"

        with patch("network.subprocess.run", return_value=mock_result):
            assert network.get_active_connection() == "MyWiFi:802-11-wireless:wlan0"

    def test_returns_empty_when_only_loopback(self):
        mock_result = MagicMock()
        mock_result.stdout = "lo:loopback:lo\n"

        with patch("network.subprocess.run", return_value=mock_result):
            assert network.get_active_connection() == ""

    def test_returns_empty_when_no_connections(self):
        mock_result = MagicMock()
        mock_result.stdout = ""

        with patch("network.subprocess.run", return_value=mock_result):
            assert network.get_active_connection() == ""


class TestGetWifiStatus:
    def test_returns_enabled(self):
        mock_result = MagicMock()
        mock_result.stdout = "enabled\n"

        with patch("network.subprocess.run", return_value=mock_result):
            assert network.get_wifi_status() == "enabled"

    def test_returns_disabled(self):
        mock_result = MagicMock()
        mock_result.stdout = "disabled\n"

        with patch("network.subprocess.run", return_value=mock_result):
            assert network.get_wifi_status() == "disabled"


class TestGetWifiNetworks:
    def test_parses_network_list(self):
        mock_result = MagicMock()
        mock_result.stdout = "HomeNet:85:WPA2:*\nCafeWifi:60:WPA2:\nOpenNet:30::\n"

        with patch("network.subprocess.run", return_value=mock_result):
            networks = network.get_wifi_networks()

            assert len(networks) == 3
            assert networks[0]["ssid"] == "HomeNet"
            assert networks[0]["signal"] == "85"
            assert networks[0]["in_use"] == "*"

    def test_deduplicates_by_ssid(self):
        mock_result = MagicMock()
        mock_result.stdout = "Net1:80:WPA2:\nNet1:60:WPA2:\nNet2:50:WPA2:\n"

        with patch("network.subprocess.run", return_value=mock_result):
            networks = network.get_wifi_networks()

            assert len(networks) == 2

    def test_skips_empty_ssids(self):
        mock_result = MagicMock()
        mock_result.stdout = ":80:WPA2:\nNet1:60:WPA2:\n"

        with patch("network.subprocess.run", return_value=mock_result):
            networks = network.get_wifi_networks()

            assert len(networks) == 1
            assert networks[0]["ssid"] == "Net1"

    def test_sorts_by_signal_descending(self):
        mock_result = MagicMock()
        mock_result.stdout = "Weak:20:WPA2:\nStrong:90:WPA2:\nMedium:50:WPA2:\n"

        with patch("network.subprocess.run", return_value=mock_result):
            networks = network.get_wifi_networks()

            assert networks[0]["ssid"] == "Strong"
            assert networks[1]["ssid"] == "Medium"
            assert networks[2]["ssid"] == "Weak"


class TestIsEnterpriseNetwork:
    def test_returns_true_for_enterprise(self):
        mock_result = MagicMock()
        mock_result.stdout = "CorpNet:WPA2 802.1X\nHomeNet:WPA2\n"

        with patch("network.subprocess.run", return_value=mock_result):
            assert network.is_enterprise_network("CorpNet") is True

    def test_returns_false_for_non_enterprise(self):
        mock_result = MagicMock()
        mock_result.stdout = "HomeNet:WPA2\n"

        with patch("network.subprocess.run", return_value=mock_result):
            assert network.is_enterprise_network("HomeNet") is False


class TestHasSavedConnection:
    def test_returns_true_when_connection_saved(self):
        mock_result = MagicMock()
        mock_result.stdout = "MyWiFi\nOtherNet\n"

        with patch("network.subprocess.run", return_value=mock_result):
            assert network.has_saved_connection("MyWiFi") is True

    def test_returns_false_when_not_saved(self):
        mock_result = MagicMock()
        mock_result.stdout = "OtherNet\n"

        with patch("network.subprocess.run", return_value=mock_result):
            assert network.has_saved_connection("MyWiFi") is False


class TestWifiSignalIcon:
    def test_in_use_icon(self):
        assert network.wifi_signal_icon(90, True) == "󰤨"

    def test_strong_signal(self):
        assert network.wifi_signal_icon(80, False) == "󰤥"

    def test_medium_signal(self):
        assert network.wifi_signal_icon(60, False) == "󰤢"

    def test_weak_signal(self):
        assert network.wifi_signal_icon(30, False) == "󰤟"

    def test_very_weak_signal(self):
        assert network.wifi_signal_icon(10, False) == "󰤯"


class TestFormatWifiNetworkLine:
    def test_formats_connected_network(self):
        net = {"ssid": "Home", "signal": "85", "security": "WPA2", "in_use": "*"}
        result = network.format_wifi_network_line(net)
        assert "Home" in result
        assert "(connected)" in result
        assert "85%" in result
        assert "󰌾" in result

    def test_formats_open_network(self):
        net = {"ssid": "Free", "signal": "50", "security": "--", "in_use": ""}
        result = network.format_wifi_network_line(net)
        assert "Free" in result
        assert "(connected)" not in result
        assert "󰌾" not in result

    def test_formats_empty_security_as_open(self):
        net = {"ssid": "Open", "signal": "40", "security": "", "in_use": ""}
        result = network.format_wifi_network_line(net)
        assert "󰌾" not in result


class TestExtractSsidFromSelection:
    def test_extracts_ssid_from_formatted_line(self):
        selection = "󰤨  HomeNet  󰌾 85% (connected)"
        assert network.extract_ssid_from_selection(selection) == "HomeNet"

    def test_extracts_ssid_without_lock_icon(self):
        selection = "󰤢  OpenNet  50%"
        assert network.extract_ssid_from_selection(selection) == "OpenNet"


class TestConnectionTypeIcon:
    def test_wireless_icon(self):
        assert network.connection_type_icon("802-11-wireless") == "󰤨"

    def test_ethernet_icon(self):
        assert network.connection_type_icon("802-3-ethernet") == "󰀂"

    def test_vpn_icon(self):
        assert network.connection_type_icon("vpn") == "󰖂"

    def test_unknown_type_icon(self):
        assert network.connection_type_icon("bridge") == "󰛳"


class TestGetActiveConnectionNames:
    def test_returns_active_names(self):
        mock_result = MagicMock()
        mock_result.stdout = "MyWiFi\nVPN\n"

        with patch("network.subprocess.run", return_value=mock_result):
            names = network.get_active_connection_names()
            assert names == {"MyWiFi", "VPN"}


class TestGetSavedConnections:
    def test_parses_connections(self):
        mock_result = MagicMock()
        mock_result.stdout = "HomeNet:802-11-wireless\nWork:802-3-ethernet\n"

        with patch("network.subprocess.run", return_value=mock_result):
            connections = network.get_saved_connections()
            assert len(connections) == 2
            assert connections[0]["name"] == "HomeNet"
            assert connections[0]["type"] == "802-11-wireless"

    def test_skips_loopback(self):
        mock_result = MagicMock()
        mock_result.stdout = "lo:loopback\nHomeNet:802-11-wireless\n"

        with patch("network.subprocess.run", return_value=mock_result):
            connections = network.get_saved_connections()
            assert len(connections) == 1
            assert connections[0]["name"] == "HomeNet"


class TestExtractConnectionNameFromSelection:
    def test_extracts_active_connection_name(self):
        selection = "󰤨  MyWiFi (active)"
        assert network.extract_connection_name_from_selection(selection) == "MyWiFi"

    def test_extracts_inactive_connection_name(self):
        selection = "󰤨  MyWiFi"
        assert network.extract_connection_name_from_selection(selection) == "MyWiFi"


class TestToggleWifi:
    def test_disables_when_enabled(self):
        with patch("network.get_wifi_status", return_value="enabled"):
            with patch("network.subprocess.run") as mock_run:
                with patch("network.notify"):
                    network.toggle_wifi()

                    mock_run.assert_called_once_with(
                        ["nmcli", "radio", "wifi", "off"],
                        capture_output=True,
                    )

    def test_enables_when_disabled(self):
        with patch("network.get_wifi_status", return_value="disabled"):
            with patch("network.subprocess.run") as mock_run:
                with patch("network.notify"):
                    network.toggle_wifi()

                    mock_run.assert_called_once_with(
                        ["nmcli", "radio", "wifi", "on"],
                        capture_output=True,
                    )


class TestConnectWifi:
    def test_uses_saved_connection_when_available(self):
        with patch("network.has_saved_connection", return_value=True):
            with patch("network.connect_to_saved_connection") as mock_connect:
                network.connect_wifi("MyWiFi")
                mock_connect.assert_called_once_with("MyWiFi")

    def test_uses_enterprise_when_detected(self):
        with patch("network.has_saved_connection", return_value=False):
            with patch("network.is_enterprise_network", return_value=True):
                with patch("network.connect_to_enterprise_wifi") as mock_connect:
                    network.connect_wifi("CorpNet")
                    mock_connect.assert_called_once_with("CorpNet")

    def test_uses_password_for_regular_network(self):
        with patch("network.has_saved_connection", return_value=False):
            with patch("network.is_enterprise_network", return_value=False):
                with patch("network.connect_to_wifi_with_password") as mock_connect:
                    network.connect_wifi("CafeWifi")
                    mock_connect.assert_called_once_with("CafeWifi")


class TestMain:
    def test_opens_settings_with_full_flag(self):
        with patch("network.sys.argv", ["cmd", "--full"]):
            with patch("network.subprocess.Popen") as mock_popen:
                network.main()

                mock_popen.assert_called_once_with(
                    ["nm-connection-editor"],
                    start_new_session=True,
                )

    def test_shows_main_menu_without_args(self):
        with patch("network.sys.argv", ["cmd"]):
            with patch("network.show_main_menu") as mock_menu:
                network.main()
                mock_menu.assert_called_once()
