import subprocess
from network_management import network_manager, network_prompts


def connect_to_saved_connection(ssid: str) -> None:
    result = subprocess.run(
        ["nmcli", "connection", "up", ssid],
        capture_output=True,
    )
    if result.returncode == 0:
        network_prompts.notify(f"Connected to {ssid}")
    else:
        network_prompts.notify(f"Failed to connect to {ssid}")


def connect_to_enterprise_wifi(ssid: str) -> None:
    identity = network_prompts.prompt_fuzzel_input(f"Username for {ssid}")
    if not identity:
        return

    password = network_prompts.prompt_fuzzel_input(f"Password for {ssid}")
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
        network_prompts.notify(f"Failed to connect to {ssid}")
        return

    up_result = subprocess.run(
        ["nmcli", "connection", "up", ssid],
        capture_output=True,
    )
    if up_result.returncode == 0:
        network_prompts.notify(f"Connected to {ssid}")
    else:
        subprocess.run(
            ["nmcli", "connection", "delete", ssid],
            capture_output=True,
        )
        network_prompts.notify(f"Failed to connect to {ssid}")


def connect_to_wifi_with_password(ssid: str) -> None:
    password = network_prompts.prompt_fuzzel_input(f"Password for {ssid}")
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
        network_prompts.notify(f"Connected to {ssid}")
    else:
        network_prompts.notify(f"Failed to connect to {ssid}")


def connect_wifi(ssid: str) -> None:
    if network_manager.has_saved_connection(ssid):
        connect_to_saved_connection(ssid)
    elif network_manager.is_enterprise_network(ssid):
        connect_to_enterprise_wifi(ssid)
    else:
        connect_to_wifi_with_password(ssid)
