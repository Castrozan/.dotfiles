{ pkgs, ... }:
{
  services.udev.packages = [
    (pkgs.writeTextFile {
      name = "corsair-slipstream-receiver-udev-rules";
      destination = "/etc/udev/rules.d/70-corsair-slipstream-receiver.rules";
      text = ''
        SUBSYSTEM=="hidraw", ATTRS{modalias}=="usb:v1B1Cp1BDC*in01", TAG+="uaccess"
      '';
    })
  ];
}
