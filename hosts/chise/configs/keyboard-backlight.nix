{ pkgs, ... }:

let
  pythonWithPyusb = pkgs.python3.withPackages (ps: [ ps.pyusb ]);

  keyboardBacklightCommonLibrary = ''
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

    MODPROBE_PATH = "${pkgs.kmod}/bin/modprobe"
    RMMOD_PATH = "${pkgs.kmod}/bin/rmmod"

    def cycle_alienware_wmi_kernel_driver():
        subprocess.run([MODPROBE_PATH, "alienware_wmi"], check=True)
        import time; time.sleep(1)
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

    def build_set_color_animation_commands(animation_id, red, green, blue, zones=ALL_SIXTEEN_ZONES):
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
  '';

  setKeyboardBacklightBrightnessScript = pkgs.writeScript "set-keyboard-backlight-brightness" ''
    #!${pythonWithPyusb}/bin/python3
    ${keyboardBacklightCommonLibrary}

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
        dimming_value = convert_brightness_percent_to_inverted_dimming_value(brightness_percent)

        cycle_alienware_wmi_kernel_driver()
        device = acquire_alienware_led_controller()

        animation_commands = build_set_color_animation_commands(
            POWER_STATE_AC_CHARGING,
            FIRMWARE_DEFAULT_CYAN_RED,
            FIRMWARE_DEFAULT_CYAN_GREEN,
            FIRMWARE_DEFAULT_CYAN_BLUE,
        )
        for command in animation_commands:
            send_hid_command(device, command)

        dimming_command = build_dimming_command(dimming_value)
        send_hid_command(device, dimming_command)
        device.reset()
        print(f"Keyboard backlight set to {brightness_percent}% (dimming={dimming_value})")

    if __name__ == "__main__":
        main()
  '';

  setKeyboardBacklightColorScript = pkgs.writeScript "set-keyboard-backlight-color" ''
    #!${pythonWithPyusb}/bin/python3
    ${keyboardBacklightCommonLibrary}

    def parse_rgb_from_arguments():
        if len(sys.argv) != 4:
            print("Usage: set-keyboard-backlight-color <red> <green> <blue>", file=sys.stderr)
            print("  Values 0-255. Uses finish_play — expect flickering.", file=sys.stderr)
            print("  Combine with set-keyboard-backlight-brightness for dimming.", file=sys.stderr)
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

        cycle_alienware_wmi_kernel_driver()
        device = acquire_alienware_led_controller()

        animation_commands = build_set_color_animation_commands(
            POWER_STATE_AC_CHARGING, red, green, blue
        )
        for command in animation_commands:
            send_hid_command(device, command)

        device.reset()
        print(f"Keyboard color set to RGB({red},{green},{blue}) — may flicker")

    if __name__ == "__main__":
        main()
  '';

  resetKeyboardBacklightScript = pkgs.writeScript "reset-keyboard-backlight" ''
    #!${pythonWithPyusb}/bin/python3
    ${keyboardBacklightCommonLibrary}

    FIRMWARE_DEFAULT_CYAN_RED = 0
    FIRMWARE_DEFAULT_CYAN_GREEN = 255
    FIRMWARE_DEFAULT_CYAN_BLUE = 255

    def main():
        cycle_alienware_wmi_kernel_driver()
        device = acquire_alienware_led_controller()

        animation_commands = build_set_color_animation_commands(
            POWER_STATE_AC_CHARGING,
            FIRMWARE_DEFAULT_CYAN_RED,
            FIRMWARE_DEFAULT_CYAN_GREEN,
            FIRMWARE_DEFAULT_CYAN_BLUE,
        )
        for command in animation_commands:
            send_hid_command(device, command)

        dimming_command = build_dimming_command(0)
        send_hid_command(device, dimming_command)

        device.reset()
        print("Keyboard backlight reset to cyan 100%")

    if __name__ == "__main__":
        main()
  '';

in
{
  environment.systemPackages = [
    (pkgs.writeShellScriptBin "set-keyboard-backlight-brightness" ''
      exec sudo ${setKeyboardBacklightBrightnessScript} "$@"
    '')
    (pkgs.writeShellScriptBin "set-keyboard-backlight-color" ''
      exec sudo ${setKeyboardBacklightColorScript} "$@"
    '')
    (pkgs.writeShellScriptBin "reset-keyboard-backlight" ''
      exec sudo ${resetKeyboardBacklightScript} "$@"
    '')
  ];

  systemd.services.dim-keyboard-backlight = {
    description = "Dim Dell G15 keyboard backlight to 5% on boot";
    wantedBy = [ "multi-user.target" ];
    after = [ "systemd-udevd.service" ];
    serviceConfig = {
      Type = "oneshot";
      ExecStart = "${setKeyboardBacklightBrightnessScript} 5";
      RemainAfterExit = true;
    };
  };
}
