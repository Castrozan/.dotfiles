import ipaddress
import json
import socket
import subprocess
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
MIDEA_DISCOVERY_PORT = 6445
SUBNET_SCAN_TIMEOUT_SECONDS = 0.5
DISCOVERY_PROBE_TIMEOUT_SECONDS = 1.5
SUBNET_SCAN_MAX_WORKERS = 128
SUBNET_SCAN_MAX_HOSTS_TOTAL = 4096
INTERFACE_NAMES_TO_SKIP_DURING_SUBNET_SCAN = {"lo", "docker0", "tailscale0"}
SMALLEST_IPV4_PREFIX_LENGTH_TO_SCAN = 20

MIDEA_V3_DISCOVERY_PACKET_BYTES = bytes.fromhex(
    "5a5a0111000020000000000000000000"
    "00000000000000000000000000000000"
    "00000000000000000000000000000000"
    "00000000000000000000000000000000"
)


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


def parse_local_ipv4_networks_from_ip_address_command_output(
    ip_address_command_output: str,
) -> list[ipaddress.IPv4Network]:
    networks: list[ipaddress.IPv4Network] = []
    for line in ip_address_command_output.splitlines():
        tokens = line.split()
        if len(tokens) < 4:
            continue
        interface_name = tokens[1]
        if interface_name in INTERFACE_NAMES_TO_SKIP_DURING_SUBNET_SCAN:
            continue
        if tokens[2] != "inet":
            continue
        cidr_token = tokens[3]
        try:
            parsed_network = ipaddress.ip_network(cidr_token, strict=False)
        except ValueError:
            continue
        if not isinstance(parsed_network, ipaddress.IPv4Network):
            continue
        if parsed_network.prefixlen < SMALLEST_IPV4_PREFIX_LENGTH_TO_SCAN:
            continue
        if parsed_network.num_addresses <= 1:
            continue
        networks.append(parsed_network)
    return networks


def discover_local_ipv4_networks() -> list[ipaddress.IPv4Network]:
    completed = subprocess.run(
        ["ip", "-4", "-o", "addr", "show", "scope", "global"],
        capture_output=True,
        text=True,
        check=True,
    )
    return parse_local_ipv4_networks_from_ip_address_command_output(completed.stdout)


def enumerate_unique_host_addresses_across_networks(
    networks: list[ipaddress.IPv4Network],
    maximum_host_addresses: int = SUBNET_SCAN_MAX_HOSTS_TOTAL,
) -> list[str]:
    already_seen_addresses: set[str] = set()
    collected_addresses: list[str] = []
    for network in networks:
        for host_address in network.hosts():
            host_address_string = str(host_address)
            if host_address_string in already_seen_addresses:
                continue
            already_seen_addresses.add(host_address_string)
            collected_addresses.append(host_address_string)
            if len(collected_addresses) >= maximum_host_addresses:
                return collected_addresses
    return collected_addresses


def scan_addresses_for_open_midea_port(addresses: list[str]) -> list[str]:
    if not addresses:
        return []
    with ThreadPoolExecutor(max_workers=SUBNET_SCAN_MAX_WORKERS) as executor:
        port_open_flags = list(executor.map(check_midea_port_open, addresses))
    return [
        address for address, port_open in zip(addresses, port_open_flags) if port_open
    ]


def probe_address_appears_to_be_midea_device(ip_address: str) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(DISCOVERY_PROBE_TIMEOUT_SECONDS)
    try:
        sock.sendto(MIDEA_V3_DISCOVERY_PACKET_BYTES, (ip_address, MIDEA_DISCOVERY_PORT))
        response_payload, _ = sock.recvfrom(4096)
    except (socket.timeout, OSError):
        return False
    finally:
        sock.close()
    return len(response_payload) >= 4 and response_payload[:2] == b"\x5a\x5a"


def filter_addresses_confirmed_as_midea_devices(addresses: list[str]) -> list[str]:
    return [
        address
        for address in addresses
        if probe_address_appears_to_be_midea_device(address)
    ]


def pick_best_midea_candidate_address(
    confirmed_midea_addresses: list[str],
    all_port_open_addresses: list[str],
) -> str | None:
    if confirmed_midea_addresses:
        chosen_pool = confirmed_midea_addresses
        unverified_extras = [
            address
            for address in all_port_open_addresses
            if address not in confirmed_midea_addresses
        ]
        if unverified_extras:
            print(
                "note: midea port open but UDP discovery silent on "
                f"{unverified_extras}",
                file=sys.stderr,
            )
    elif all_port_open_addresses:
        chosen_pool = all_port_open_addresses
        print(
            "warning: no UDP 6445 confirmation, falling back to TCP-only "
            f"candidates {all_port_open_addresses}",
            file=sys.stderr,
        )
    else:
        return None
    if len(chosen_pool) > 1:
        print(
            f"warning: multiple midea candidates {chosen_pool}, "
            f"picking {chosen_pool[0]}",
            file=sys.stderr,
        )
    return chosen_pool[0]


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

    local_networks = discover_local_ipv4_networks()
    if not local_networks:
        print("no local IPv4 networks available to scan", file=sys.stderr)
        raise SystemExit(1)

    networks_summary = ", ".join(str(network) for network in local_networks)
    print(
        f"scanning local subnets {networks_summary} for midea device...",
        file=sys.stderr,
    )

    candidate_addresses = enumerate_unique_host_addresses_across_networks(
        local_networks
    )
    port_open_addresses = scan_addresses_for_open_midea_port(candidate_addresses)
    confirmed_midea_addresses = filter_addresses_confirmed_as_midea_devices(
        port_open_addresses
    )
    discovered_ip = pick_best_midea_candidate_address(
        confirmed_midea_addresses, port_open_addresses
    )

    if discovered_ip is None:
        print("device not found on any local subnet", file=sys.stderr)
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
