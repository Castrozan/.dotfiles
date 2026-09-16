from network_management import network_display


class TestWifiSignalIcon:
    def test_in_use_icon(self):
        assert network_display.wifi_signal_icon(90, True) == "󰤨"

    def test_strong_signal(self):
        assert network_display.wifi_signal_icon(80, False) == "󰤥"

    def test_medium_signal(self):
        assert network_display.wifi_signal_icon(60, False) == "󰤢"

    def test_weak_signal(self):
        assert network_display.wifi_signal_icon(30, False) == "󰤟"

    def test_very_weak_signal(self):
        assert network_display.wifi_signal_icon(10, False) == "󰤯"


class TestFormatWifiNetworkLine:
    def test_formats_connected_network(self):
        net = {"ssid": "Home", "signal": "85", "security": "WPA2", "in_use": "*"}
        result = network_display.format_wifi_network_line(net)
        assert "Home" in result
        assert "(connected)" in result
        assert "85%" in result
        assert "󰌾" in result

    def test_formats_open_network(self):
        net = {"ssid": "Free", "signal": "50", "security": "--", "in_use": ""}
        result = network_display.format_wifi_network_line(net)
        assert "Free" in result
        assert "(connected)" not in result
        assert "󰌾" not in result

    def test_formats_empty_security_as_open(self):
        net = {"ssid": "Open", "signal": "40", "security": "", "in_use": ""}
        result = network_display.format_wifi_network_line(net)
        assert "󰌾" not in result


class TestExtractSsidFromSelection:
    def test_extracts_ssid_from_formatted_line(self):
        selection = "󰤨  HomeNet  󰌾 85% (connected)"
        assert network_display.extract_ssid_from_selection(selection) == "HomeNet"

    def test_extracts_ssid_without_lock_icon(self):
        selection = "󰤢  OpenNet  50%"
        assert network_display.extract_ssid_from_selection(selection) == "OpenNet"


class TestConnectionTypeIcon:
    def test_wireless_icon(self):
        assert network_display.connection_type_icon("802-11-wireless") == "󰤨"

    def test_ethernet_icon(self):
        assert network_display.connection_type_icon("802-3-ethernet") == "󰀂"

    def test_vpn_icon(self):
        assert network_display.connection_type_icon("vpn") == "󰖂"

    def test_unknown_type_icon(self):
        assert network_display.connection_type_icon("bridge") == "󰛳"


class TestExtractConnectionNameFromSelection:
    def test_extracts_active_connection_name(self):
        selection = "󰤨  MyWiFi (active)"
        assert (
            network_display.extract_connection_name_from_selection(selection)
            == "MyWiFi"
        )

    def test_extracts_inactive_connection_name(self):
        selection = "󰤨  MyWiFi"
        assert (
            network_display.extract_connection_name_from_selection(selection)
            == "MyWiFi"
        )
