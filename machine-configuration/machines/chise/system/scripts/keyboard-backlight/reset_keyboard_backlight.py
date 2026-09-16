import alienware_led_controller


FIRMWARE_DEFAULT_CYAN_RED = 0
FIRMWARE_DEFAULT_CYAN_GREEN = 255
FIRMWARE_DEFAULT_CYAN_BLUE = 255


def main():
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

    dimming_command = alienware_led_controller.build_dimming_command(0)
    alienware_led_controller.send_hid_command(device, dimming_command)

    device.reset()
    print("Keyboard backlight reset to cyan 100%")


if __name__ == "__main__":
    main()
