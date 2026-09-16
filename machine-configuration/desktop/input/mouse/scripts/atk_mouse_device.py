import os
import select
import time
from pathlib import Path

ATK_VENDOR_ID = "373b"
ATK_HID_REPORT_ID = 0x08
ATK_CMD_GET_EEPROM = 0x08
ATK_CMD_SET_EEPROM = 0x07


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


def read_sysfs_attribute(path: Path, default: str = "unknown") -> str:
    try:
        return path.read_text().strip()
    except OSError:
        return default
