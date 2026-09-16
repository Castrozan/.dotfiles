import sys

import atk_mouse_device

RATE_DEFINITIONS = {
    "8k": (0x40, 0x15),
    "8000": (0x40, 0x15),
    "4k": (0x20, 0x35),
    "4000": (0x20, 0x35),
    "2k": (0x10, 0x45),
    "2000": (0x10, 0x45),
    "1k": (0x01, 0x54),
    "1000": (0x01, 0x54),
}

RATE_DISPLAY_NAMES = {
    (0x40, 0x15): "8000Hz",
    (0x20, 0x35): "4000Hz",
    (0x10, 0x45): "2000Hz",
    (0x01, 0x54): "1000Hz",
}


def decode_rate_value(rate_hi: int, rate_lo: int) -> str:
    return RATE_DISPLAY_NAMES.get(
        (rate_hi, rate_lo), f"unknown (0x{rate_hi:02x}{rate_lo:02x})"
    )


def rate_argument_to_bytes(rate_argument: str) -> tuple[int, int]:
    if rate_argument not in RATE_DEFINITIONS:
        raise SystemExit(f"Invalid rate: {rate_argument} (use 1k, 2k, 4k, or 8k)")
    return RATE_DEFINITIONS[rate_argument]


def get_current_rate() -> str:
    hidraw_path = atk_mouse_device.find_atk_hidraw_config_interface()
    command = atk_mouse_device.build_atk_command(
        atk_mouse_device.ATK_CMD_GET_EEPROM, 0x00, 0x00, 0x06
    )
    response = atk_mouse_device.send_and_receive_atk_command(hidraw_path, command)
    return decode_rate_value(response[6], response[7])


def set_rate(rate_argument: str) -> None:
    target_hi, target_lo = rate_argument_to_bytes(rate_argument)
    target_name = decode_rate_value(target_hi, target_lo)

    hidraw_path = atk_mouse_device.find_atk_hidraw_config_interface()
    get_command = atk_mouse_device.build_atk_command(
        atk_mouse_device.ATK_CMD_GET_EEPROM, 0x00, 0x00, 0x06
    )

    current_response = atk_mouse_device.send_and_receive_atk_command(
        hidraw_path, get_command
    )

    current_rate_name = decode_rate_value(current_response[6], current_response[7])
    print(f"Current rate: {current_rate_name}")

    if current_response[6] == target_hi and current_response[7] == target_lo:
        print(f"Already at {target_name}")
        return

    data_bytes = [target_hi, target_lo] + list(current_response[8:12])
    set_command = atk_mouse_device.build_atk_command(
        atk_mouse_device.ATK_CMD_SET_EEPROM, 0x00, 0x00, 0x06, data_bytes
    )

    print(f"Setting rate to {target_name}...")
    try:
        atk_mouse_device.send_and_receive_atk_command(hidraw_path, set_command)
    except SystemExit:
        print("No response (device may have re-enumerated)", file=sys.stderr)
        return

    try:
        verify_response = atk_mouse_device.send_and_receive_atk_command(
            hidraw_path, get_command
        )
    except SystemExit:
        print("Cannot verify (device may have re-enumerated)", file=sys.stderr)
        return

    new_rate_name = decode_rate_value(verify_response[6], verify_response[7])
    print(f"New rate: {new_rate_name}")

    if verify_response[6] == target_hi and verify_response[7] == target_lo:
        print("Rate changed successfully")
    else:
        print(
            f"Rate verification failed (expected {target_name}, got {new_rate_name})",
            file=sys.stderr,
        )
        raise SystemExit(1)


def show_device_info() -> None:
    usb_device_path = atk_mouse_device.find_atk_usb_device_path()

    product = atk_mouse_device.read_sysfs_attribute(usb_device_path / "product")
    vendor_id = atk_mouse_device.read_sysfs_attribute(usb_device_path / "idVendor")
    product_id = atk_mouse_device.read_sysfs_attribute(usb_device_path / "idProduct")
    usb_speed = atk_mouse_device.read_sysfs_attribute(usb_device_path / "speed")
    usb_version = atk_mouse_device.read_sysfs_attribute(
        usb_device_path / "version"
    ).replace(" ", "")

    print(f"Device: {product}")
    print(f"USB ID: {vendor_id}:{product_id}")
    print(f"USB Speed: {usb_speed} Mbps")
    print(f"USB Version: {usb_version}")

    speed_descriptions = {
        "480": "Mode: High Speed (supports up to 8000Hz)",
        "12": "Mode: Full Speed (max 1000Hz)",
    }
    print(speed_descriptions.get(usb_speed, "Mode: Unknown"))

    try:
        hidraw_path = atk_mouse_device.find_atk_hidraw_config_interface()
        print(f"Config interface: {hidraw_path}")
    except SystemExit:
        print("Config interface: not found")
        return

    try:
        current_rate = get_current_rate()
        print(f"EEPROM poll rate: {current_rate}")
    except SystemExit:
        print("EEPROM poll rate: unable to read")


def print_usage() -> None:
    print("Usage: mouse-poll-rate <get|set|info>", file=sys.stderr)
    print("  get          Show current polling rate", file=sys.stderr)
    print("  set <rate>   Set rate (1k, 2k, 4k, 8k)", file=sys.stderr)
    print("  info         Show device and USB info", file=sys.stderr)


def main() -> None:
    if len(sys.argv) < 2:
        print_usage()
        raise SystemExit(1)

    subcommand = sys.argv[1]

    if subcommand == "get":
        print(get_current_rate())
    elif subcommand == "set":
        if len(sys.argv) < 3:
            print("Usage: mouse-poll-rate set <1k|2k|4k|8k>", file=sys.stderr)
            raise SystemExit(1)
        set_rate(sys.argv[2])
    elif subcommand == "info":
        show_device_info()
    else:
        print_usage()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
