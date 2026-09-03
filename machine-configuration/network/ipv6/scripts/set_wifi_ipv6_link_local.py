from __future__ import annotations

import plistlib
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

NETWORK_PREFERENCES_PATH = Path(
    "/Library/Preferences/SystemConfiguration/preferences.plist"
)
WIFI_NETWORK_SERVICE_NAME = "Wi-Fi"
LINK_LOCAL_CONFIG_METHOD = "LinkLocal"
NETWORKSETUP_BINARY_PATH = "/usr/sbin/networksetup"

CommandRunner = Callable[[Sequence[str]], None]


def run_command(command: Sequence[str]) -> None:
    subprocess.run(list(command), check=True)


def read_wifi_ipv6_config_method(preferences_path: Path) -> str | None:
    if not preferences_path.exists():
        return None
    with preferences_path.open("rb") as preferences_file:
        preferences = plistlib.load(preferences_file)
    for network_service in preferences.get("NetworkServices", {}).values():
        if network_service.get("UserDefinedName") == WIFI_NETWORK_SERVICE_NAME:
            return network_service.get("IPv6", {}).get("ConfigMethod", "")
    return None


def reconcile_wifi_ipv6_link_local(
    preferences_path: Path = NETWORK_PREFERENCES_PATH,
    run: CommandRunner = run_command,
) -> bool:
    config_method = read_wifi_ipv6_config_method(preferences_path)
    if config_method is None:
        print("no Wi-Fi network service found; leaving IPv6 untouched", file=sys.stderr)
        return False
    if config_method == LINK_LOCAL_CONFIG_METHOD:
        return False
    print(
        f"setting Wi-Fi IPv6 to link-local only (was {config_method or 'unset'})...",
        file=sys.stderr,
    )
    run([NETWORKSETUP_BINARY_PATH, "-setv6LinkLocal", WIFI_NETWORK_SERVICE_NAME])
    return True


def main() -> int:
    reconcile_wifi_ipv6_link_local()
    return 0


if __name__ == "__main__":
    sys.exit(main())
