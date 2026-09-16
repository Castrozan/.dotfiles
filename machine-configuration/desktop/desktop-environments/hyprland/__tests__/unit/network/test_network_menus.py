from types import SimpleNamespace
from unittest.mock import Mock

import network
import pytest


@pytest.fixture
def network_ports(monkeypatch):
    ports = SimpleNamespace()
    for owner, names in [
        (network.network_prompts, ["notify", "show_fuzzel_menu"]),
        (
            network.network_manager,
            [
                "get_wifi_networks",
                "rescan_wifi",
                "disconnect_from_network",
                "delete_connection",
                "get_saved_connections",
                "get_active_connection_names",
                "get_wifi_status",
                "get_active_connection",
                "toggle_wifi",
            ],
        ),
        (network.wifi_connection, ["connect_wifi"]),
        (network.subprocess, ["run", "Popen"]),
    ]:
        for name in names:
            port = Mock()
            monkeypatch.setattr(owner, name, port)
            setattr(ports, name, port)
    ports.show_fuzzel_menu.return_value = ""
    ports.get_wifi_status.return_value = "enabled"
    ports.get_active_connection.return_value = "Office:wifi"
    return ports


@pytest.mark.parametrize(
    "action,target",
    [
        ("WiFi Networks", "show_wifi_networks"),
        ("Saved Connections", "show_connections"),
        ("Open Settings", None),
        ("Disable WiFi", "toggle_wifi"),
        ("", None),
    ],
)
def test_main_menu_routes_selection(network_ports, monkeypatch, action, target):
    ports = network_ports
    ports.show_fuzzel_menu.side_effect = [action, ""]
    if target in {"show_wifi_networks", "show_connections"}:
        handler = Mock()
        monkeypatch.setattr(network, target, handler)
    network.show_main_menu()
    arguments = ports.show_fuzzel_menu.call_args_list[0].args
    assert arguments[0] == "Network"
    assert "Office" in arguments[1]
    assert "Disable WiFi" in arguments[1]
    if target in {"show_wifi_networks", "show_connections"}:
        handler.assert_called_once_with()
    elif target == "toggle_wifi":
        ports.toggle_wifi.assert_called_once_with()
        assert ports.show_fuzzel_menu.call_count == 2
    elif action == "Open Settings":
        ports.Popen.assert_called_once_with(
            ["nm-connection-editor"], start_new_session=True
        )
    else:
        ports.Popen.assert_not_called()
    ports.get_wifi_status.return_value = "disabled"
    ports.get_active_connection.return_value = ""
    ports.show_fuzzel_menu.side_effect = None
    ports.show_fuzzel_menu.return_value = ""
    network.show_main_menu()
    assert "Enable WiFi" in ports.show_fuzzel_menu.call_args.args[1]


@pytest.mark.parametrize(
    "connected,selection",
    [(False, "Office"), (True, "Office (connected)"), (False, "")],
)
def test_wifi_selection_connects_or_disconnects(
    network_ports, monkeypatch, connected, selection
):
    ports = network_ports
    ports.get_wifi_networks.return_value = [{"ssid": "Office"}]
    monkeypatch.setattr(
        network.network_display, "format_wifi_network_line", lambda item: "Office"
    )
    monkeypatch.setattr(
        network.network_display, "extract_ssid_from_selection", lambda item: "Office"
    )
    return_to_menu = Mock()
    monkeypatch.setattr(network, "show_main_menu", return_to_menu)
    ports.show_fuzzel_menu.side_effect = [selection, "Disconnect"]
    network.show_wifi_networks()
    ports.rescan_wifi.assert_called_once_with()
    if connected:
        ports.disconnect_from_network.assert_called_once_with("Office")
    elif selection:
        ports.connect_wifi.assert_called_once_with("Office")
    else:
        ports.connect_wifi.assert_not_called()
    return_to_menu.assert_called_once_with()
    ports.get_wifi_networks.return_value = []
    network.show_wifi_networks()
    ports.notify.assert_called_with("No WiFi networks found")


@pytest.mark.parametrize(
    "active,action,returncode",
    [
        (True, "Disconnect", 0),
        (True, "Delete", 0),
        (False, "Connect", 0),
        (False, "Connect", 1),
        (False, "Delete", 0),
    ],
)
def test_connection_actions_preserve_names_and_report_failures(
    network_ports, active, action, returncode
):
    ports = network_ports
    ports.show_fuzzel_menu.return_value = action
    ports.run.return_value = SimpleNamespace(returncode=returncode)
    function = (
        network.show_active_connection_actions
        if active
        else network.show_inactive_connection_actions
    )
    function("Office connection")
    if action == "Delete":
        ports.delete_connection.assert_called_once_with("Office connection")
    elif action == "Disconnect":
        ports.disconnect_from_network.assert_called_once_with("Office connection")
    else:
        ports.run.assert_called_once_with(
            ["nmcli", "connection", "up", "Office connection"], capture_output=True
        )
        ports.notify.assert_called_once_with(
            ("Connected to " if returncode == 0 else "Failed to connect to ")
            + "Office connection"
        )


@pytest.mark.parametrize(
    "selection,active", [("Office (active)", True), ("Home", False), ("", False)]
)
def test_saved_connections_choose_active_and_inactive_actions(
    network_ports, monkeypatch, selection, active
):
    ports = network_ports
    ports.get_saved_connections.return_value = [
        {"name": "Office", "type": "wifi"},
        {"name": "Home", "type": "wifi"},
    ]
    ports.get_active_connection_names.return_value = ["Office"]
    ports.show_fuzzel_menu.return_value = selection
    monkeypatch.setattr(
        network.network_display,
        "extract_connection_name_from_selection",
        lambda value: value.split()[0],
    )
    active_action, inactive_action, main_menu = Mock(), Mock(), Mock()
    monkeypatch.setattr(network, "show_active_connection_actions", active_action)
    monkeypatch.setattr(network, "show_inactive_connection_actions", inactive_action)
    monkeypatch.setattr(network, "show_main_menu", main_menu)
    network.show_connections()
    if selection:
        (active_action if active else inactive_action).assert_called_once_with(
            "Office" if active else "Home"
        )
    else:
        active_action.assert_not_called()
        inactive_action.assert_not_called()
    assert "Office (active)" in ports.show_fuzzel_menu.call_args.args[1]
    main_menu.assert_called_once_with()
    ports.get_saved_connections.return_value = []
    network.show_connections()
    ports.notify.assert_called_with("No saved connections")
