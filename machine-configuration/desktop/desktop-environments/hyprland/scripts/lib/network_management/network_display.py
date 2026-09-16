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


def connection_type_icon(connection_type: str) -> str:
    if "wireless" in connection_type:
        return "󰤨"
    if "ethernet" in connection_type:
        return "󰀂"
    if "vpn" in connection_type:
        return "󰖂"
    return "󰛳"


def extract_connection_name_from_selection(selection: str) -> str:
    without_icon = selection.split("  ", 1)
    if len(without_icon) < 2:
        return ""
    name = without_icon[1].strip()
    if name.endswith(" (active)"):
        name = name[: -len(" (active)")]
    return name
