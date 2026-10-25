import sys
from dataclasses import dataclass

import hid

CORSAIR_VENDOR_ID = 0x1B1C
SLIPSTREAM_RECEIVER_PRODUCT_ID = 0x1BDC
VENDOR_USAGE_PAGE = 0xFF42
COMMAND_USAGE = 0x01
WIRELESS_DEVICE_ENDPOINT = 0x09
REPORT_SIZE = 64
SET_PROPERTY_COMMAND = 0x01
GET_PROPERTY_COMMAND = 0x02
BRIGHTNESS_PROPERTY = 0x02
LIGHTING_MODE_PROPERTY = 0x03
HARDWARE_LIGHTING_MODE = 0x01
SOFTWARE_LIGHTING_MODE = 0x02
MAXIMUM_BRIGHTNESS = 1000
RESPONSE_TIMEOUT_MILLISECONDS = 1000
MAXIMUM_UNRELATED_REPORTS = 8


class CorsairMouseError(Exception):
    pass


@dataclass(frozen=True)
class PropertyResponse:
    status: int
    value: int


def find_receiver_command_interface_path():
    for interface in hid.enumerate(CORSAIR_VENDOR_ID, SLIPSTREAM_RECEIVER_PRODUCT_ID):
        if (
            interface["usage_page"] == VENDOR_USAGE_PAGE
            and interface["usage"] == COMMAND_USAGE
        ):
            return interface["path"]
    raise CorsairMouseError("Corsair Slipstream receiver 1b1c:1bdc is not connected")


def exchange_property_command(device, command, property_id, value_bytes=b""):
    report = (
        bytes([0x00, WIRELESS_DEVICE_ENDPOINT, command, property_id, 0x00])
        + value_bytes
    )
    device.write(report.ljust(REPORT_SIZE + 1, b"\x00"))
    for _ in range(MAXIMUM_UNRELATED_REPORTS):
        response = device.read(REPORT_SIZE, timeout=RESPONSE_TIMEOUT_MILLISECONDS)
        if not response:
            raise CorsairMouseError(
                "the mouse did not answer; move it to wake it and retry"
            )
        if response[1] == command:
            return PropertyResponse(
                status=response[2], value=int.from_bytes(response[3:5], "little")
            )
    raise CorsairMouseError("the receiver kept sending unrelated reports")


def get_property(device, property_id):
    response = exchange_property_command(device, GET_PROPERTY_COMMAND, property_id)
    if response.status:
        raise CorsairMouseError(
            f"reading property 0x{property_id:02x} failed with status {response.status}"
        )
    return response.value


def set_property(device, property_id, value):
    response = exchange_property_command(
        device, SET_PROPERTY_COMMAND, property_id, value.to_bytes(2, "little")
    )
    if response.status:
        raise CorsairMouseError(
            f"writing property 0x{property_id:02x} failed with status {response.status}"
        )


def store_onboard_brightness(device, brightness):
    set_property(device, LIGHTING_MODE_PROPERTY, SOFTWARE_LIGHTING_MODE)
    try:
        set_property(device, BRIGHTNESS_PROPERTY, brightness)
    finally:
        set_property(device, LIGHTING_MODE_PROPERTY, HARDWARE_LIGHTING_MODE)
    return get_property(device, BRIGHTNESS_PROPERTY)


def parse_requested_brightness(arguments):
    if not arguments:
        return None
    if len(arguments) > 1 or not arguments[0].isdigit():
        raise CorsairMouseError(
            f"usage: corsair-mouse-brightness [0-{MAXIMUM_BRIGHTNESS}]"
        )
    brightness = int(arguments[0])
    if brightness > MAXIMUM_BRIGHTNESS:
        raise CorsairMouseError(
            f"brightness must be between 0 and {MAXIMUM_BRIGHTNESS}"
        )
    return brightness


def main():
    try:
        requested_brightness = parse_requested_brightness(sys.argv[1:])
        with hid.Device(path=find_receiver_command_interface_path()) as device:
            if requested_brightness is None:
                print(get_property(device, BRIGHTNESS_PROPERTY))
            else:
                print(store_onboard_brightness(device, requested_brightness))
    except (CorsairMouseError, hid.HIDException) as error:
        print(f"corsair-mouse-brightness: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
