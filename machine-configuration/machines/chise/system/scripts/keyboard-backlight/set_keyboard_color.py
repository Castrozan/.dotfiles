import sys

import alienware_led_controller


def parse_rgb_from_arguments():
    if len(sys.argv) != 4:
        print(
            "Usage: set-keyboard-backlight-color <red> <green> <blue>", file=sys.stderr
        )
        print("  Values 0-255. Uses finish_play — expect flickering.", file=sys.stderr)
        print(
            "  Combine with set-keyboard-backlight-brightness for dimming.",
            file=sys.stderr,
        )
        sys.exit(1)
    red = int(sys.argv[1])
    green = int(sys.argv[2])
    blue = int(sys.argv[3])
    for name, value in [("red", red), ("green", green), ("blue", blue)]:
        if not 0 <= value <= 255:
            print(f"{name} must be 0-255", file=sys.stderr)
            sys.exit(1)
    return red, green, blue


def main():
    red, green, blue = parse_rgb_from_arguments()

    alienware_led_controller.cycle_alienware_wmi_kernel_driver()
    device = alienware_led_controller.acquire_alienware_led_controller()

    animation_commands = alienware_led_controller.build_set_color_animation_commands(
        alienware_led_controller.POWER_STATE_AC_CHARGING, red, green, blue
    )
    for command in animation_commands:
        alienware_led_controller.send_hid_command(device, command)

    device.reset()
    print(f"Keyboard color set to RGB({red},{green},{blue}) — may flicker")


if __name__ == "__main__":
    main()
