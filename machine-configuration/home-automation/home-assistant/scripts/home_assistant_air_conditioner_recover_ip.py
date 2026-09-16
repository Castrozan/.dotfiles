import json
import sys
from pathlib import Path

import midea_device_discovery
from home_assistant_client import (
    make_home_assistant_api_request,
    read_home_assistant_token,
)

HOME_ASSISTANT_CONFIG_ENTRIES_PATH = (
    Path.home() / ".homeassistant" / ".storage" / "core.config_entries"
)
MIDEA_INTEGRATION_DOMAIN = "midea_ac_lan"


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

    if midea_device_discovery.check_midea_port_open(configured_ip):
        print("no recovery needed")
        return

    local_networks = midea_device_discovery.discover_local_ipv4_networks()
    if not local_networks:
        print("no local IPv4 networks available to scan", file=sys.stderr)
        raise SystemExit(1)

    networks_summary = ", ".join(str(network) for network in local_networks)
    print(
        f"scanning local subnets {networks_summary} for midea device...",
        file=sys.stderr,
    )

    candidate_addresses = (
        midea_device_discovery.enumerate_unique_host_addresses_across_networks(
            local_networks
        )
    )
    port_open_addresses = midea_device_discovery.scan_addresses_for_open_midea_port(
        candidate_addresses
    )
    confirmed_midea_addresses = (
        midea_device_discovery.filter_addresses_confirmed_as_midea_devices(
            port_open_addresses
        )
    )
    discovered_ip = midea_device_discovery.pick_best_midea_candidate_address(
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
