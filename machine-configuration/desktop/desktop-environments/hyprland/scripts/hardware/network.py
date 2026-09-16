import subprocess
import sys
from network_management import (
    network_display,
    network_manager,
    network_prompts,
    wifi_connection,
)


def show_wifi_networks() -> None:
    network_prompts.notify("Scanning for networks...")
    network_manager.rescan_wifi()

    networks = network_manager.get_wifi_networks()
    if not networks:
        network_prompts.notify("No WiFi networks found")
        show_main_menu()
        return

    formatted_lines = [network_display.format_wifi_network_line(n) for n in networks]
    formatted = "\n".join(formatted_lines)
    lines = min(len(formatted_lines), 10)

    selection = network_prompts.show_fuzzel_menu("WiFi Networks", formatted, lines)
    if selection:
        ssid = network_display.extract_ssid_from_selection(selection)
        if "(connected)" in selection:
            action = network_prompts.show_fuzzel_menu(
                ssid, "󰤮  Disconnect\n  Cancel", 2
            )
            if "Disconnect" in action:
                network_manager.disconnect_from_network(ssid)
        else:
            wifi_connection.connect_wifi(ssid)

    show_main_menu()


def show_active_connection_actions(name: str) -> None:
    action = network_prompts.show_fuzzel_menu(
        name,
        "󰤮  Disconnect\n  Delete\n  Cancel",
        3,
    )
    if "Disconnect" in action:
        network_manager.disconnect_from_network(name)
    elif "Delete" in action:
        network_manager.delete_connection(name)


def show_inactive_connection_actions(name: str) -> None:
    action = network_prompts.show_fuzzel_menu(
        name,
        "󰤨  Connect\n  Delete\n  Cancel",
        3,
    )
    if "Connect" in action:
        result = subprocess.run(
            ["nmcli", "connection", "up", name],
            capture_output=True,
        )
        if result.returncode == 0:
            network_prompts.notify(f"Connected to {name}")
        else:
            network_prompts.notify(f"Failed to connect to {name}")
    elif "Delete" in action:
        network_manager.delete_connection(name)


def show_connections() -> None:
    connections = network_manager.get_saved_connections()
    if not connections:
        network_prompts.notify("No saved connections")
        show_main_menu()
        return

    active_names = network_manager.get_active_connection_names()
    formatted_lines = []
    for conn in connections:
        icon = network_display.connection_type_icon(conn["type"])
        if conn["name"] in active_names:
            formatted_lines.append(f"{icon}  {conn['name']} (active)")
        else:
            formatted_lines.append(f"{icon}  {conn['name']}")

    formatted = "\n".join(formatted_lines)
    lines = min(len(formatted_lines), 8)

    selection = network_prompts.show_fuzzel_menu("Connections", formatted, lines)
    if selection:
        name = network_display.extract_connection_name_from_selection(selection)
        if "(active)" in selection:
            show_active_connection_actions(name)
        else:
            show_inactive_connection_actions(name)

    show_main_menu()


def show_main_menu() -> None:
    wifi_status = network_manager.get_wifi_status()
    if wifi_status == "enabled":
        wifi_icon = "󰤨"
        wifi_text = "Disable WiFi"
    else:
        wifi_icon = "󰤮"
        wifi_text = "Enable WiFi"

    active = network_manager.get_active_connection()
    active_text = ""
    if active:
        name = active.split(":")[0]
        active_text = f" ({name})"

    options = (
        f"󰤢  WiFi Networks{active_text}\n"
        f"󰛳  Saved Connections\n"
        f"{wifi_icon}  {wifi_text}\n"
        f"󰒓  Open Settings"
    )

    selection = network_prompts.show_fuzzel_menu("Network", options, 4)
    if "WiFi Networks" in selection:
        show_wifi_networks()
    elif "Saved" in selection:
        show_connections()
    elif "WiFi" in selection:
        network_manager.toggle_wifi()
        show_main_menu()
    elif "Settings" in selection:
        subprocess.Popen(
            ["nm-connection-editor"],
            start_new_session=True,
        )


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        subprocess.Popen(
            ["nm-connection-editor"],
            start_new_session=True,
        )
    else:
        show_main_menu()


if __name__ == "__main__":
    main()
