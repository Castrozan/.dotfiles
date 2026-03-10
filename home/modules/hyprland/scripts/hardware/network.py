import subprocess
import sys
import time


def show_fuzzel_menu(prompt: str, options: str, lines: int = 5) -> str:
    result = subprocess.run(
        [
            "hypr-fuzzel",
            "--dmenu",
            "--width",
            "40",
            "--lines",
            str(lines),
            "--prompt",
            f"{prompt}> ",
        ],
        input=options,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def get_active_connection() -> str:
    result = subprocess.run(
        ["nmcli", "-t", "-f", "NAME,TYPE,DEVICE", "connection", "show", "--active"],
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        if not line.startswith("lo"):
            return line
    return ""


def get_wifi_status() -> str:
    result = subprocess.run(
        ["nmcli", "radio", "wifi"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def get_wifi_networks() -> list[dict[str, str]]:
    result = subprocess.run(
        [
            "nmcli",
            "-t",
            "-f",
            "SSID,SIGNAL,SECURITY,IN-USE",
            "device",
            "wifi",
            "list",
            "--rescan",
            "no",
        ],
        capture_output=True,
        text=True,
    )
    seen_ssids: set[str] = set()
    networks: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        parts = line.split(":")
        if len(parts) < 4 or not parts[0]:
            continue
        ssid = parts[0]
        if ssid in seen_ssids:
            continue
        seen_ssids.add(ssid)
        networks.append(
            {
                "ssid": ssid,
                "signal": parts[1],
                "security": parts[2],
                "in_use": parts[3],
            }
        )
    networks.sort(key=lambda n: int(n["signal"] or "0"), reverse=True)
    return networks


def rescan_wifi() -> None:
    subprocess.run(
        ["nmcli", "device", "wifi", "rescan"],
        capture_output=True,
    )
    time.sleep(2)


def is_enterprise_network(ssid: str) -> bool:
    result = subprocess.run(
        [
            "nmcli",
            "-t",
            "-f",
            "SSID,SECURITY",
            "device",
            "wifi",
            "list",
            "--rescan",
            "no",
        ],
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        if line.startswith(f"{ssid}:") and "802.1X" in line:
            return True
    return False


def has_saved_connection(ssid: str) -> bool:
    result = subprocess.run(
        ["nmcli", "-t", "-f", "NAME", "connection", "show"],
        capture_output=True,
        text=True,
    )
    return ssid in result.stdout.splitlines()


def notify(message: str) -> None:
    subprocess.run(
        ["notify-send", "-t", "2000", "Network", message],
        capture_output=True,
    )


def prompt_fuzzel_input(prompt_text: str) -> str:
    result = subprocess.run(
        [
            "hypr-fuzzel",
            "--dmenu",
            "--width",
            "30",
            "--lines",
            "0",
            "--prompt",
            f"{prompt_text}> ",
        ],
        input="",
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def connect_to_saved_connection(ssid: str) -> None:
    result = subprocess.run(
        ["nmcli", "connection", "up", ssid],
        capture_output=True,
    )
    if result.returncode == 0:
        notify(f"Connected to {ssid}")
    else:
        notify(f"Failed to connect to {ssid}")


def connect_to_enterprise_wifi(ssid: str) -> None:
    identity = prompt_fuzzel_input(f"Username for {ssid}")
    if not identity:
        return

    password = prompt_fuzzel_input(f"Password for {ssid}")
    if not password:
        return

    add_result = subprocess.run(
        [
            "nmcli",
            "connection",
            "add",
            "type",
            "wifi",
            "con-name",
            ssid,
            "ssid",
            ssid,
            "wifi-sec.key-mgmt",
            "wpa-eap",
            "802-1x.eap",
            "peap",
            "802-1x.phase2-auth",
            "mschapv2",
            "802-1x.identity",
            identity,
            "802-1x.password",
            password,
        ],
        capture_output=True,
    )
    if add_result.returncode != 0:
        notify(f"Failed to connect to {ssid}")
        return

    up_result = subprocess.run(
        ["nmcli", "connection", "up", ssid],
        capture_output=True,
    )
    if up_result.returncode == 0:
        notify(f"Connected to {ssid}")
    else:
        subprocess.run(
            ["nmcli", "connection", "delete", ssid],
            capture_output=True,
        )
        notify(f"Failed to connect to {ssid}")


def connect_to_wifi_with_password(ssid: str) -> None:
    password = prompt_fuzzel_input(f"Password for {ssid}")
    if not password:
        return

    result = subprocess.run(
        [
            "nmcli",
            "device",
            "wifi",
            "connect",
            ssid,
            "password",
            password,
        ],
        capture_output=True,
    )
    if result.returncode == 0:
        notify(f"Connected to {ssid}")
    else:
        notify(f"Failed to connect to {ssid}")


def connect_wifi(ssid: str) -> None:
    if has_saved_connection(ssid):
        connect_to_saved_connection(ssid)
    elif is_enterprise_network(ssid):
        connect_to_enterprise_wifi(ssid)
    else:
        connect_to_wifi_with_password(ssid)


def wifi_signal_icon(signal: int, in_use: bool) -> str:
    if in_use:
        return "󰤨"
    if signal >= 75:
        return "󰤥"
    if signal >= 50:
        return "󰤢"
    if signal >= 25:
        return "󰤟"
    return "󰤯"


def format_wifi_network_line(network: dict[str, str]) -> str:
    signal = int(network["signal"] or "0")
    in_use = network["in_use"] == "*"
    icon = wifi_signal_icon(signal, in_use)

    lock = ""
    security = network["security"]
    if security and security != "--":
        lock = "󰌾 "

    if in_use:
        return f"{icon}  {network['ssid']}  {lock}{signal}% (connected)"
    return f"{icon}  {network['ssid']}  {lock}{signal}%"


def extract_ssid_from_selection(selection: str) -> str:
    without_icon = selection.split("  ", 1)
    if len(without_icon) < 2:
        return ""
    rest = without_icon[1]
    ssid_end = rest.find("  ")
    if ssid_end == -1:
        return rest.strip()
    return rest[:ssid_end].strip()


def disconnect_from_network(name: str) -> None:
    result = subprocess.run(
        ["nmcli", "connection", "down", name],
        capture_output=True,
    )
    if result.returncode == 0:
        notify(f"Disconnected from {name}")


def delete_connection(name: str) -> None:
    result = subprocess.run(
        ["nmcli", "connection", "delete", name],
        capture_output=True,
    )
    if result.returncode == 0:
        notify(f"Deleted {name}")


def show_wifi_networks() -> None:
    notify("Scanning for networks...")
    rescan_wifi()

    networks = get_wifi_networks()
    if not networks:
        notify("No WiFi networks found")
        show_main_menu()
        return

    formatted_lines = [format_wifi_network_line(n) for n in networks]
    formatted = "\n".join(formatted_lines)
    lines = min(len(formatted_lines), 10)

    selection = show_fuzzel_menu("WiFi Networks", formatted, lines)
    if selection:
        ssid = extract_ssid_from_selection(selection)
        if "(connected)" in selection:
            action = show_fuzzel_menu(ssid, "󰤮  Disconnect\n  Cancel", 2)
            if "Disconnect" in action:
                disconnect_from_network(ssid)
        else:
            connect_wifi(ssid)

    show_main_menu()


def connection_type_icon(connection_type: str) -> str:
    if "wireless" in connection_type:
        return "󰤨"
    if "ethernet" in connection_type:
        return "󰀂"
    if "vpn" in connection_type:
        return "󰖂"
    return "󰛳"


def get_active_connection_names() -> set[str]:
    result = subprocess.run(
        ["nmcli", "-t", "-f", "NAME", "connection", "show", "--active"],
        capture_output=True,
        text=True,
    )
    return set(result.stdout.strip().splitlines())


def get_saved_connections() -> list[dict[str, str]]:
    result = subprocess.run(
        ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"],
        capture_output=True,
        text=True,
    )
    connections: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        if line.startswith("lo"):
            continue
        parts = line.split(":", 1)
        if len(parts) < 2 or not parts[0]:
            continue
        connections.append({"name": parts[0], "type": parts[1]})
    return connections


def show_active_connection_actions(name: str) -> None:
    action = show_fuzzel_menu(
        name,
        "󰤮  Disconnect\n  Delete\n  Cancel",
        3,
    )
    if "Disconnect" in action:
        disconnect_from_network(name)
    elif "Delete" in action:
        delete_connection(name)


def show_inactive_connection_actions(name: str) -> None:
    action = show_fuzzel_menu(
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
            notify(f"Connected to {name}")
        else:
            notify(f"Failed to connect to {name}")
    elif "Delete" in action:
        delete_connection(name)


def extract_connection_name_from_selection(selection: str) -> str:
    without_icon = selection.split("  ", 1)
    if len(without_icon) < 2:
        return ""
    name = without_icon[1].strip()
    if name.endswith(" (active)"):
        name = name[: -len(" (active)")]
    return name


def show_connections() -> None:
    connections = get_saved_connections()
    if not connections:
        notify("No saved connections")
        show_main_menu()
        return

    active_names = get_active_connection_names()
    formatted_lines = []
    for conn in connections:
        icon = connection_type_icon(conn["type"])
        if conn["name"] in active_names:
            formatted_lines.append(f"{icon}  {conn['name']} (active)")
        else:
            formatted_lines.append(f"{icon}  {conn['name']}")

    formatted = "\n".join(formatted_lines)
    lines = min(len(formatted_lines), 8)

    selection = show_fuzzel_menu("Connections", formatted, lines)
    if selection:
        name = extract_connection_name_from_selection(selection)
        if "(active)" in selection:
            show_active_connection_actions(name)
        else:
            show_inactive_connection_actions(name)

    show_main_menu()


def toggle_wifi() -> None:
    if get_wifi_status() == "enabled":
        subprocess.run(["nmcli", "radio", "wifi", "off"], capture_output=True)
        notify("WiFi disabled")
    else:
        subprocess.run(["nmcli", "radio", "wifi", "on"], capture_output=True)
        notify("WiFi enabled")


def show_main_menu() -> None:
    wifi_status = get_wifi_status()
    if wifi_status == "enabled":
        wifi_icon = "󰤨"
        wifi_text = "Disable WiFi"
    else:
        wifi_icon = "󰤮"
        wifi_text = "Enable WiFi"

    active = get_active_connection()
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

    selection = show_fuzzel_menu("Network", options, 4)
    if "WiFi Networks" in selection:
        show_wifi_networks()
    elif "Saved" in selection:
        show_connections()
    elif "WiFi" in selection:
        toggle_wifi()
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
