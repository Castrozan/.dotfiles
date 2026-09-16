import sys
import subprocess
import usb.core
import usb.util

ALIENWARE_LED_CONTROLLER_VENDOR_ID = 0x187C
ALIENWARE_LED_CONTROLLER_PRODUCT_ID = 0x0550
HID_REPORT_LENGTH = 33
ALL_SIXTEEN_ZONES = list(range(16))


def send_hid_command(device, command_hex_string):
    data = bytearray.fromhex("03" + command_hex_string)
    data += bytearray(HID_REPORT_LENGTH - len(data))
    device.ctrl_transfer(0x21, 0x09, 0x0200, 0x00, data)
    return bytearray(device.ctrl_transfer(0xA1, 0x01, 0x0100, 0x00, HID_REPORT_LENGTH))


MODPROBE_PATH = "@modprobe@"
RMMOD_PATH = "@rmmod@"


def cycle_alienware_wmi_kernel_driver():
    subprocess.run([MODPROBE_PATH, "alienware_wmi"], check=True)
    import time

    time.sleep(1)
    subprocess.run([RMMOD_PATH, "alienware_wmi"], check=True)
    time.sleep(1)


def acquire_alienware_led_controller():
    device = usb.core.find(
        idVendor=ALIENWARE_LED_CONTROLLER_VENDOR_ID,
        idProduct=ALIENWARE_LED_CONTROLLER_PRODUCT_ID,
    )
    if device is None:
        print("Alienware LED controller (187c:0550) not found", file=sys.stderr)
        sys.exit(1)
    device.reset()
    interface_number = device[0].interfaces()[0].bInterfaceNumber
    if device.is_kernel_driver_active(interface_number):
        device.detach_kernel_driver(interface_number)
    return device


def build_zone_hex_string(zones=ALL_SIXTEEN_ZONES):
    return "".join(f"{z:02x}" for z in zones)


def build_dimming_command(dimming_value, zones=ALL_SIXTEEN_ZONES):
    zone_hex = build_zone_hex_string(zones)
    return f"26{dimming_value:02x}{len(zones):04x}{zone_hex}"


def build_set_color_animation_commands(
    animation_id, red, green, blue, zones=ALL_SIXTEEN_ZONES
):
    zone_hex = build_zone_hex_string(zones)
    return [
        f"2200040000{animation_id:04x}",
        f"2200010000{animation_id:04x}",
        f"23010010{zone_hex}",
        f"2400ffff0001{red:02x}{green:02x}{blue:02x}",
        f"2200030000{animation_id:04x}",
        f"2200060000{animation_id:04x}",
    ]


POWER_STATE_AC_CHARGING = 0x5D
