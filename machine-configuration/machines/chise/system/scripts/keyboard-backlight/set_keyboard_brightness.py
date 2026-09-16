import sys

import alienware_led_controller


DIMMING_SCALE_INVERTED_FULL_BRIGHT = 0
DIMMING_SCALE_INVERTED_FULL_OFF = 100


def parse_brightness_percentage_from_arguments():
    if len(sys.argv) != 2:
        print("Usage: set-keyboard-backlight-brightness <0-100>", file=sys.stderr)
        print("  0   = off (fully dimmed)", file=sys.stderr)
        print("  5   = 5% brightness (recommended low)", file=sys.stderr)
        print("  100 = full brightness (firmware default)", file=sys.stderr)
        sys.exit(1)
    brightness_percent = int(sys.argv[1])
    if not 0 <= brightness_percent <= 100:
        print("Brightness must be 0-100", file=sys.stderr)
        sys.exit(1)
    return brightness_percent


def convert_brightness_percent_to_inverted_dimming_value(brightness_percent):
    return DIMMING_SCALE_INVERTED_FULL_OFF - brightness_percent


FIRMWARE_DEFAULT_CYAN_RED = 0
FIRMWARE_DEFAULT_CYAN_GREEN = 255
FIRMWARE_DEFAULT_CYAN_BLUE = 255


def main():
    brightness_percent = parse_brightness_percentage_from_arguments()
    dimming_value = convert_brightness_percent_to_inverted_dimming_value(
        brightness_percent
    )

    alienware_led_controller.cycle_alienware_wmi_kernel_driver()
    device = alienware_led_controller.acquire_alienware_led_controller()

    animation_commands = alienware_led_controller.build_set_color_animation_commands(
        alienware_led_controller.POWER_STATE_AC_CHARGING,
        FIRMWARE_DEFAULT_CYAN_RED,
        FIRMWARE_DEFAULT_CYAN_GREEN,
        FIRMWARE_DEFAULT_CYAN_BLUE,
    )
    for command in animation_commands:
        alienware_led_controller.send_hid_command(device, command)

    dimming_command = alienware_led_controller.build_dimming_command(dimming_value)
    alienware_led_controller.send_hid_command(device, dimming_command)
    device.reset()
    print(f"Keyboard backlight set to {brightness_percent}% (dimming={dimming_value})")


if __name__ == "__main__":
    main()
