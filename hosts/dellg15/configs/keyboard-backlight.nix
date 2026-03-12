{ pkgs, ... }:

let
  pythonWithPyusb = pkgs.python3.withPackages (ps: [ ps.pyusb ]);

  disableKeyboardBacklightScript = pkgs.writeScript "disable-keyboard-backlight" ''
    #!${pythonWithPyusb}/bin/python3
    import sys
    import usb.core
    import usb.util

    ALIENWARE_LED_CONTROLLER_VENDOR_ID = 0x187C
    ALIENWARE_LED_CONTROLLER_PRODUCT_ID = 0x0550

    HID_SET_REPORT_REQUEST_TYPE = 0x21
    HID_SET_REPORT_REQUEST = 0x09
    HID_SET_REPORT_VALUE = 0x0200
    HID_GET_REPORT_REQUEST_TYPE = 0xA1
    HID_GET_REPORT_REQUEST = 0x01
    HID_GET_REPORT_VALUE = 0x0100

    HID_REPORT_LENGTH = 33

    COMMAND_PREFIX = 0x03
    COMMAND_SET_COLOR = 0x27
    COMMAND_DIMMING = 0x26
    COMMAND_USER_ANIMATION = 0x21
    COMMAND_POWER_ANIMATION = 0x22
    ANIMATION_REMOVE = 0x04


    def send_hid_command(device, command_bytes):
        report = bytearray([COMMAND_PREFIX] + command_bytes)
        report += bytearray(HID_REPORT_LENGTH - len(report))
        device.ctrl_transfer(
            HID_SET_REPORT_REQUEST_TYPE,
            HID_SET_REPORT_REQUEST,
            HID_SET_REPORT_VALUE,
            0x00,
            report,
        )
        return bytearray(
            device.ctrl_transfer(
                HID_GET_REPORT_REQUEST_TYPE,
                HID_GET_REPORT_REQUEST,
                HID_GET_REPORT_VALUE,
                0x00,
                HID_REPORT_LENGTH,
            )
        )


    def query_zone_count(device):
        response = send_hid_command(device, [0x20, 0x02])
        return response[2]


    def remove_all_animations(device):
        send_hid_command(device, [COMMAND_USER_ANIMATION, ANIMATION_REMOVE])
        send_hid_command(device, [COMMAND_POWER_ANIMATION, ANIMATION_REMOVE])


    def set_all_zones_to_black(device, zone_count):
        for zone_id in range(zone_count):
            send_hid_command(device, [COMMAND_SET_COLOR, 0x00, 0x00, 0x00, zone_id])


    def set_brightness_to_zero(device):
        send_hid_command(device, [COMMAND_DIMMING, 0x00])


    def find_alienware_led_controller():
        return usb.core.find(
            idVendor=ALIENWARE_LED_CONTROLLER_VENDOR_ID,
            idProduct=ALIENWARE_LED_CONTROLLER_PRODUCT_ID,
        )


    def detach_kernel_driver_if_active(device):
        if device.is_kernel_driver_active(0):
            device.detach_kernel_driver(0)


    def main():
        device = find_alienware_led_controller()
        if device is None:
            print("Alienware LED controller (187c:0550) not found", file=sys.stderr)
            sys.exit(1)

        detach_kernel_driver_if_active(device)
        usb.util.claim_interface(device, 0)

        try:
            zone_count = query_zone_count(device)
            remove_all_animations(device)
            set_all_zones_to_black(device, zone_count)
            set_brightness_to_zero(device)
            print(f"Keyboard backlight disabled ({zone_count} zones)")
        finally:
            usb.util.release_interface(device, 0)


    if __name__ == "__main__":
        main()
  '';
in
{
  systemd.services.disable-keyboard-backlight = {
    description = "Disable Dell G15 Alienware keyboard backlight via USB HID";
    wantedBy = [ "multi-user.target" ];
    after = [ "systemd-udevd.service" ];
    serviceConfig = {
      Type = "oneshot";
      ExecStart = disableKeyboardBacklightScript;
      RemainAfterExit = true;
    };
  };
}
