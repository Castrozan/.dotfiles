import os
import select
import sys
import time
from pathlib import Path

ATK_VENDOR_ID = "373b"
ATK_HID_REPORT_ID = 0x08
ATK_CMD_GET_EEPROM = 0x08
ATK_CMD_SET_EEPROM = 0x07

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


def find_atk_hidraw_config_interface() -> str:
    hidraw_base = Path("/sys/class/hidraw")
    if not hidraw_base.exists():
        raise SystemExit("No ATK mouse found (sysfs hidraw not available)")

    for hidraw_sysfs in sorted(hidraw_base.iterdir()):
        try:
            vendor = (
                (hidraw_sysfs / "device" / ".." / ".." / "idVendor")
                .resolve()
                .read_text()
                .strip()
            )
            interface_number = (
                (hidraw_sysfs / "device" / ".." / "bInterfaceNumber")
                .resolve()
                .read_text()
                .strip()
            )
        except (OSError, ValueError):
            continue

        if vendor == ATK_VENDOR_ID and interface_number == "01":
            return f"/dev/{hidraw_sysfs.name}"

    raise SystemExit(f"No ATK mouse found (vendor {ATK_VENDOR_ID}, interface 1)")


def find_atk_usb_device_path() -> Path:
    usb_devices = Path("/sys/bus/usb/devices")
    for usb_device in sorted(usb_devices.iterdir()):
        try:
            vendor = (usb_device / "idVendor").read_text().strip()
        except (OSError, ValueError):
            continue
        if vendor == ATK_VENDOR_ID:
            return usb_device

    raise SystemExit("No ATK mouse dongle found")


def compute_atk_checksum(packet_bytes: list[int]) -> int:
    return (0x55 - sum(packet_bytes)) & 0xFF


def build_atk_command(
    command_id: int,
    eeprom_addr_hi: int,
    eeprom_addr_lo: int,
    data_length: int,
    data_bytes: list[int] | None = None,
) -> bytes:
    if data_bytes is None:
        data_bytes = []

    packet = [
        ATK_HID_REPORT_ID,
        command_id,
        0x00,
        eeprom_addr_hi,
        eeprom_addr_lo,
        data_length,
    ]

    for i in range(10):
        if i < len(data_bytes):
            packet.append(data_bytes[i])
        else:
            packet.append(0x00)

    checksum = compute_atk_checksum(packet)
    packet.append(checksum)

    return bytes(packet)


def send_and_receive_atk_command(hidraw_path: str, command: bytes) -> bytes:
    fd = os.open(hidraw_path, os.O_RDWR | os.O_NONBLOCK)
    try:
        while True:
            ready, _, _ = select.select([fd], [], [], 0.02)
            if not ready:
                break
            os.read(fd, 64)

        os.write(fd, command)

        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            ready, _, _ = select.select([fd], [], [], 0.1)
            if not ready:
                continue
            try:
                while True:
                    response = os.read(fd, 64)
                    if (
                        len(response) >= 2
                        and response[0] == 0x08
                        and response[1] in (0x07, 0x08)
                    ):
                        return response
            except BlockingIOError:
                pass

        raise SystemExit("No response from device")
    finally:
        os.close(fd)


def decode_rate_value(rate_hi: int, rate_lo: int) -> str:
    return RATE_DISPLAY_NAMES.get(
        (rate_hi, rate_lo), f"unknown (0x{rate_hi:02x}{rate_lo:02x})"
    )


def rate_argument_to_bytes(rate_argument: str) -> tuple[int, int]:
    if rate_argument not in RATE_DEFINITIONS:
        raise SystemExit(f"Invalid rate: {rate_argument} (use 1k, 2k, 4k, or 8k)")
    return RATE_DEFINITIONS[rate_argument]


def get_current_rate() -> str:
    hidraw_path = find_atk_hidraw_config_interface()
    command = build_atk_command(ATK_CMD_GET_EEPROM, 0x00, 0x00, 0x06)
    response = send_and_receive_atk_command(hidraw_path, command)
    return decode_rate_value(response[6], response[7])


def set_rate(rate_argument: str) -> None:
    target_hi, target_lo = rate_argument_to_bytes(rate_argument)
    target_name = decode_rate_value(target_hi, target_lo)

    hidraw_path = find_atk_hidraw_config_interface()
    get_command = build_atk_command(ATK_CMD_GET_EEPROM, 0x00, 0x00, 0x06)

    current_response = send_and_receive_atk_command(hidraw_path, get_command)

    current_rate_name = decode_rate_value(current_response[6], current_response[7])
    print(f"Current rate: {current_rate_name}")

    if current_response[6] == target_hi and current_response[7] == target_lo:
        print(f"Already at {target_name}")
        return

    data_bytes = [target_hi, target_lo] + list(current_response[8:12])
    set_command = build_atk_command(ATK_CMD_SET_EEPROM, 0x00, 0x00, 0x06, data_bytes)

    print(f"Setting rate to {target_name}...")
    try:
        send_and_receive_atk_command(hidraw_path, set_command)
    except SystemExit:
        print("No response (device may have re-enumerated)", file=sys.stderr)
        return

    try:
        verify_response = send_and_receive_atk_command(hidraw_path, get_command)
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


def read_sysfs_attribute(path: Path, default: str = "unknown") -> str:
    try:
        return path.read_text().strip()
    except OSError:
        return default


def show_device_info() -> None:
    usb_device_path = find_atk_usb_device_path()

    product = read_sysfs_attribute(usb_device_path / "product")
    vendor_id = read_sysfs_attribute(usb_device_path / "idVendor")
    product_id = read_sysfs_attribute(usb_device_path / "idProduct")
    usb_speed = read_sysfs_attribute(usb_device_path / "speed")
    usb_version = read_sysfs_attribute(usb_device_path / "version").replace(" ", "")

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
        hidraw_path = find_atk_hidraw_config_interface()
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
