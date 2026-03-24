import json
import socket
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HOME_ASSISTANT_BASE_URL = "http://localhost:8123"
HOME_ASSISTANT_TOKEN_PATH = Path.home() / ".secrets" / "home-assistant-token"
HOME_ASSISTANT_CONFIG_ENTRIES_PATH = (
    Path.home() / ".homeassistant" / ".storage" / "core.config_entries"
)
MIDEA_INTEGRATION_DOMAIN = "midea_ac_lan"
MIDEA_LAN_PORT = 6444
SUBNET_SCAN_TIMEOUT_SECONDS = 0.5
SUBNET_SCAN_MAX_WORKERS = 50


def read_home_assistant_token() -> str:
    token_file = HOME_ASSISTANT_TOKEN_PATH
    if not token_file.is_file():
        print(
            f"Home Assistant token not found at {token_file}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return token_file.read_text().strip()


def make_home_assistant_api_request(
    token: str, endpoint: str, payload: dict | None = None
) -> dict | list | None:
    url = f"{HOME_ASSISTANT_BASE_URL}{endpoint}"
    data = json.dumps(payload).encode() if payload else None
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST" if payload is not None else "GET",
    )
    response = urllib.request.urlopen(request)
    body = response.read().decode()
    if body:
        return json.loads(body)
    return None


def read_midea_config_entry() -> dict:
    config_path = HOME_ASSISTANT_CONFIG_ENTRIES_PATH
    if not config_path.is_file():
        print(
            f"Home Assistant config not found at {config_path}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    config = json.loads(config_path.read_text())
    for entry in config.get("data", {}).get("entries", []):
        if entry.get("domain") == MIDEA_INTEGRATION_DOMAIN:
            return entry
    print(
        f"No {MIDEA_INTEGRATION_DOMAIN} entry found in config",
        file=sys.stderr,
    )
    raise SystemExit(1)


def check_midea_port_open(ip_address: str) -> bool:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(SUBNET_SCAN_TIMEOUT_SECONDS)
        result = sock.connect_ex((ip_address, MIDEA_LAN_PORT))
        sock.close()
        return result == 0
    except OSError:
        return False


def scan_single_host(ip_address: str) -> str | None:
    if check_midea_port_open(ip_address):
        return ip_address
    return None


def scan_subnet_for_midea_device(subnet_prefix: str) -> str | None:
    candidate_ips = [f"{subnet_prefix}.{host_id}" for host_id in range(1, 255)]
    with ThreadPoolExecutor(max_workers=SUBNET_SCAN_MAX_WORKERS) as executor:
        for result in executor.map(scan_single_host, candidate_ips):
            if result is not None:
                return result
    return None


def derive_subnet_prefix(ip_address: str) -> str:
    octets = ip_address.split(".")
    return ".".join(octets[:3])


def update_midea_config_entry_ip_address(new_ip_address: str) -> None:
    config_path = HOME_ASSISTANT_CONFIG_ENTRIES_PATH
    config = json.loads(config_path.read_text())
    for entry in config.get("data", {}).get("entries", []):
        if entry.get("domain") == MIDEA_INTEGRATION_DOMAIN:
            entry["data"]["ip_address"] = new_ip_address
            break
    config_path.write_text(json.dumps(config, indent=2))


def reload_midea_integration(token: str, entry_id: str) -> bool:
    try:
        endpoint = f"/api/config/config_entries/entry/{entry_id}/reload"
        make_home_assistant_api_request(token, endpoint, {})
        return True
    except Exception:
        return False


def main() -> None:
    midea_entry = read_midea_config_entry()
    configured_ip = midea_entry["data"]["ip_address"]
    entry_id = midea_entry["entry_id"]

    if check_midea_port_open(configured_ip):
        print("no recovery needed")
        return

    subnet_prefix = derive_subnet_prefix(configured_ip)
    print(
        f"scanning {subnet_prefix}.0/24 for midea device...",
        file=sys.stderr,
    )
    discovered_ip = scan_subnet_for_midea_device(subnet_prefix)

    if discovered_ip is None:
        print("device not found on subnet", file=sys.stderr)
        raise SystemExit(1)

    if discovered_ip == configured_ip:
        print("no recovery needed")
        return

    update_midea_config_entry_ip_address(discovered_ip)

    token = read_home_assistant_token()
    reloaded = reload_midea_integration(token, entry_id)
    if not reloaded:
        print(
            "warning: could not reload integration, restart HA manually",
            file=sys.stderr,
        )

    print(f"recovered: {configured_ip} -> {discovered_ip}")


if __name__ == "__main__":
    main()
