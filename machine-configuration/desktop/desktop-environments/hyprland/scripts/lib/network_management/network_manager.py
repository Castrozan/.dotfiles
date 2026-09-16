import subprocess
import time
from network_management import network_prompts


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


def disconnect_from_network(name: str) -> None:
    result = subprocess.run(
        ["nmcli", "connection", "down", name],
        capture_output=True,
    )
    if result.returncode == 0:
        network_prompts.notify(f"Disconnected from {name}")


def delete_connection(name: str) -> None:
    result = subprocess.run(
        ["nmcli", "connection", "delete", name],
        capture_output=True,
    )
    if result.returncode == 0:
        network_prompts.notify(f"Deleted {name}")


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


def toggle_wifi() -> None:
    if get_wifi_status() == "enabled":
        subprocess.run(["nmcli", "radio", "wifi", "off"], capture_output=True)
        network_prompts.notify("WiFi disabled")
    else:
        subprocess.run(["nmcli", "radio", "wifi", "on"], capture_output=True)
        network_prompts.notify("WiFi enabled")
